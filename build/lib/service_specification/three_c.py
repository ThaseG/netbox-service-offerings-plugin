"""3C (Completeness, Correctness, Compliance) CMDB health engine.

run_health_check() evaluates every in-scope CI (Device, Virtual Machine,
Cluster, Cluster Group) once and stores the result as a ThreeCSnapshot plus
one ThreeCFinding per failing CI per KPI. It's called by the scheduled job
(jobs.ThreeCHealthJob); nothing here runs on page load.

Scoring follows the ServiceNow CMDB Health model: each sub-metric counts
failed CIs out of the CIs evaluated for it, failures are pooled (no
weighting) into one ratio per KPI, failure_rate = ROUND(failures * 100 /
total), and the score shown is 100 - failure_rate (N/A when total is 0).
The composite score is the average of the KPI scores that aren't N/A.

Raw [failures, total] counts are stored per CI class and tenant (see
ThreeCSnapshot.breakdown) so the report can re-pool them for any filter
without re-running the checks.
"""

import re
from collections import defaultdict
from datetime import timedelta

from dcim.constants import NONCONNECTABLE_IFACE_TYPES
from dcim.models import Device, DeviceType, Interface
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import capfirst
from extras.models import CustomField
from virtualization.models import Cluster, ClusterGroup, VirtualMachine

from .choices import ThreeCCITypeChoices, ThreeCConditionChoices, ThreeCKPIChoices, ThreeCRuleTypeChoices
from .models import (
    AppService,
    ClusterGroupServiceInfo,
    ClusterServiceInfo,
    DeviceServiceInfo,
    Service,
    ServiceOffering,
    ThreeCFinding,
    ThreeCRule,
    ThreeCSettings,
    ThreeCSnapshot,
    VirtualMachineServiceInfo,
)

__all__ = (
    'CI_MODELS',
    'KPI_SUB_METRICS',
    'aggregate_breakdown',
    'get_parameter_choices',
    'get_parameter_label',
    'health_score',
    'kpi_scores',
    'resolve_parameter',
    'rule_passes',
    'run_health_check',
    'threshold_state',
)

CI_MODELS = {
    ThreeCCITypeChoices.CI_DEVICE: Device,
    ThreeCCITypeChoices.CI_VIRTUAL_MACHINE: VirtualMachine,
    ThreeCCITypeChoices.CI_CLUSTER: Cluster,
    ThreeCCITypeChoices.CI_CLUSTER_GROUP: ClusterGroup,
}

# (Service Specification side table, its OneToOne field back to the CI)
INFO_MODELS = {
    ThreeCCITypeChoices.CI_DEVICE: (DeviceServiceInfo, 'device'),
    ThreeCCITypeChoices.CI_VIRTUAL_MACHINE: (VirtualMachineServiceInfo, 'virtual_machine'),
    ThreeCCITypeChoices.CI_CLUSTER: (ClusterServiceInfo, 'cluster'),
    ThreeCCITypeChoices.CI_CLUSTER_GROUP: (ClusterGroupServiceInfo, 'cluster_group'),
}

# Staleness is status-based, not last_updated-based: the collector flips
# unreachable devices to offline/failed, while healthy devices can go
# months without any change. VMs and Cluster Groups aren't measured (no
# collector-driven status / no status at all); Clusters have no 'failed'.
STALE_STATUSES = {
    ThreeCCITypeChoices.CI_DEVICE: ('offline', 'failed'),
    ThreeCCITypeChoices.CI_CLUSTER: ('offline',),
}

SUB_REQUIRED = 'required'
SUB_RECOMMENDED = 'recommended'
SUB_STALE = 'stale'
SUB_ORPHAN = 'orphan'
SUB_DUPLICATE = 'duplicate'
SUB_AUDIT = 'audit'

KPI_SUB_METRICS = {
    ThreeCKPIChoices.KPI_COMPLETENESS: (SUB_REQUIRED, SUB_RECOMMENDED),
    ThreeCKPIChoices.KPI_CORRECTNESS: (SUB_STALE, SUB_ORPHAN, SUB_DUPLICATE),
    ThreeCKPIChoices.KPI_COMPLIANCE: (SUB_AUDIT,),
}

SUB_METRIC_LABELS = {
    SUB_REQUIRED: 'Required',
    SUB_RECOMMENDED: 'Recommended',
    SUB_STALE: 'Stale',
    SUB_ORPHAN: 'Orphan',
    SUB_DUPLICATE: 'Duplicate',
    SUB_AUDIT: 'Audit',
}

CUSTOM_FIELD_PREFIX = 'cf_'
SERVICE_INFO_PREFIX = 'service_info__'
SERVICE_INFO_ACCESSOR = 'service_specification_info'
SERVICE_INFO_FIELDS = ('lifecycle', 'application_services', 'business_unit', 'support_group', 'change_group')

# Bookkeeping fields that are always set (or never meaningful) — offering
# them as rule parameters would only produce rules that can't fail.
EXCLUDED_PARAMETERS = {'id', 'created', 'last_updated', 'custom_field_data'}

UNCABLED_INTERFACES_SHOWN = 5


#
# Rule parameters
#


def _is_parameter_field(field):
    if field.name in EXCLUDED_PARAMETERS or field.name.startswith('_') or field.name.endswith('_count'):
        return False
    if isinstance(field, GenericForeignKey):
        return True
    if field.auto_created and not field.concrete:
        # Reverse relations (e.g. Device.interfaces) — not a property of the CI itself.
        return False
    return field.concrete or field.many_to_many


def _field_label(field):
    return capfirst(str(getattr(field, 'verbose_name', None) or field.name.replace('_', ' ')))


def get_parameter_choices(ci_type):
    """(key, label) pairs of every parameter a 3C rule can check for this
    CI class: the core model's own fields, its custom fields, and the
    fields of its Service Specification tab."""
    model = CI_MODELS.get(ci_type)
    if model is None:
        return []

    choices = sorted(
        ((field.name, _field_label(field)) for field in model._meta.get_fields() if _is_parameter_field(field)),
        key=lambda choice: choice[1].lower(),
    )
    choices += [
        (f'{CUSTOM_FIELD_PREFIX}{cf.name}', f'Custom Field: {cf.label or cf.name}')
        for cf in CustomField.objects.get_for_model(model)
    ]
    info_model, _fk_name = INFO_MODELS[ci_type]
    choices += [
        (f'{SERVICE_INFO_PREFIX}{name}', f'Service Specification: {_field_label(info_model._meta.get_field(name))}')
        for name in SERVICE_INFO_FIELDS
    ]
    return choices


def get_parameter_label(ci_type, key, _cache=None):
    if _cache is not None:
        if ci_type not in _cache:
            _cache[ci_type] = dict(get_parameter_choices(ci_type))
        return _cache[ci_type].get(key, key)
    return dict(get_parameter_choices(ci_type)).get(key, key)


def _service_info(ci):
    # Reverse OneToOne accessor: raises <Model>.DoesNotExist when unset, but
    # Django deliberately makes that exception also an AttributeError so
    # getattr()'s default kicks in.
    return getattr(ci, SERVICE_INFO_ACCESSOR, None)


def _flatten(raw, field=None):
    """Normalize any field value into (display strings, comparison tokens).
    Tokens are lowercased and include, for related objects, their name,
    primary key and slug, and for choice fields both the stored value and
    its label — so a rule's value can be written whichever way is natural
    ("active" or "Active", a tenant's name or its ID)."""
    items = raw if isinstance(raw, (list, tuple, set)) else [raw]
    choices = {}
    if field is not None and getattr(field, 'choices', None):
        choices = {str(k): str(v) for k, v in field.flatchoices}

    display, tokens = [], set()
    for item in items:
        if item is None:
            continue
        if isinstance(item, models.Model):
            text = str(item)
            display.append(text)
            tokens.update((text.lower(), str(item.pk)))
            if slug := getattr(item, 'slug', None):
                tokens.add(str(slug).lower())
            continue
        if isinstance(item, (dict, list)) and not item:
            continue
        text = str(item).strip()
        if not text:
            continue
        label = choices.get(text)
        display.append(label or text)
        tokens.add(text.lower())
        if label:
            tokens.add(label.lower())
    return display, tokens


def resolve_parameter(ci, key):
    """Return (display strings, comparison tokens) for one rule parameter
    of one CI. An empty display list means the parameter is empty."""
    if key.startswith(CUSTOM_FIELD_PREFIX):
        return _flatten((ci.custom_field_data or {}).get(key[len(CUSTOM_FIELD_PREFIX) :]))

    obj, name = ci, key
    if key.startswith(SERVICE_INFO_PREFIX):
        obj, name = _service_info(ci), key[len(SERVICE_INFO_PREFIX) :]
        if obj is None:
            return [], set()

    try:
        field = obj._meta.get_field(name)
    except FieldDoesNotExist:
        return [], set()
    if field.many_to_many:
        raw = list(getattr(obj, name).all())
    else:
        raw = getattr(obj, name, None)
    return _flatten(raw, field)


def rule_passes(rule, display, tokens):
    """Whether a CI satisfies a rule, given resolve_parameter()'s output.
    Rules state what must hold — the CI fails when this returns False."""
    condition = rule.condition
    if rule.rule_type != ThreeCRuleTypeChoices.TYPE_COMPLIANCE:
        condition = ThreeCConditionChoices.CONDITION_NOT_EMPTY

    if condition == ThreeCConditionChoices.CONDITION_NOT_EMPTY:
        return bool(display)
    if condition == ThreeCConditionChoices.CONDITION_EMPTY:
        return not display

    value = rule.value.strip()
    if condition == ThreeCConditionChoices.CONDITION_EQUALS:
        return value.lower() in tokens
    if condition == ThreeCConditionChoices.CONDITION_NOT_EQUALS:
        return value.lower() not in tokens
    options = {option.strip().lower() for option in value.split(',') if option.strip()}
    if condition == ThreeCConditionChoices.CONDITION_IN:
        return bool(options & tokens)
    if condition == ThreeCConditionChoices.CONDITION_NOT_IN:
        return not options & tokens
    if condition == ThreeCConditionChoices.CONDITION_REGEX:
        # An empty value is matched as '', so a pattern like '^$|...' can
        # leave blanks to a completeness rule instead of failing them twice.
        return any(re.search(value, text) for text in display or [''])
    return True


#
# Scoring
#


def health_score(failures, total):
    """100 - ROUND(failures * 100 / total), rounding half up like
    ServiceNow's ROUND(); None (N/A) when nothing was evaluated."""
    if not total:
        return None
    return 100 - int(failures * 100 / total + 0.5)


def _mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return int(sum(values) / len(values) + 0.5)


def threshold_state(score, lower, upper):
    """Best / At Risk / Critical for a health score, using the failure-rate
    thresholds from ThreeCSettings (failure rate = 100 - score)."""
    if score is None:
        return None
    failure_rate = 100 - score
    if failure_rate < lower:
        return 'best'
    if failure_rate > upper:
        return 'critical'
    return 'at_risk'


def aggregate_breakdown(breakdown, ci_types=None, tenant_ids=None):
    """Sum a snapshot's {ci_type: {tenant: {sub_metric: [f, t]}}} counts
    into {sub_metric: [failures, total]}, optionally limited to some CI
    classes and/or tenants (tenant IDs as strings)."""
    totals = defaultdict(lambda: [0, 0])
    for ci_type, tenants in (breakdown or {}).items():
        if ci_types and ci_type not in ci_types:
            continue
        for tenant_id, sub_metrics in tenants.items():
            if tenant_ids and tenant_id not in tenant_ids:
                continue
            for sub_metric, (failures, total) in sub_metrics.items():
                totals[sub_metric][0] += failures
                totals[sub_metric][1] += total
    return dict(totals)


def kpi_scores(sub_metric_totals):
    """{kpi: score} plus 'composite' from aggregate_breakdown()'s output."""
    scores = {}
    for kpi, sub_metrics in KPI_SUB_METRICS.items():
        failures = sum(sub_metric_totals.get(s, (0, 0))[0] for s in sub_metrics)
        total = sum(sub_metric_totals.get(s, (0, 0))[1] for s in sub_metrics)
        scores[kpi] = health_score(failures, total)
    scores['composite'] = _mean(scores[kpi] for kpi in KPI_SUB_METRICS)
    return scores


#
# Correctness helpers
#


def _lifecycle_lookups():
    """Device types with a Hardware Lifecycle, and Devices/VMs with a
    support contract assignment, from the optional netbox-lifecycle plugin.
    None when it isn't installed — those two checks are then skipped."""
    if not apps.is_installed('netbox_lifecycle'):
        return None
    hardware_lifecycle = apps.get_model('netbox_lifecycle', 'HardwareLifecycle')
    contract_assignment = apps.get_model('netbox_lifecycle', 'SupportContractAssignment')
    return {
        'device_types': set(
            hardware_lifecycle.objects.filter(
                assigned_object_type=ContentType.objects.get_for_model(DeviceType)
            ).values_list('assigned_object_id', flat=True)
        ),
        'contracts': {
            ThreeCCITypeChoices.CI_DEVICE: set(
                contract_assignment.objects.filter(device__isnull=False).values_list('device_id', flat=True)
            ),
            ThreeCCITypeChoices.CI_VIRTUAL_MACHINE: set(
                contract_assignment.objects.filter(virtual_machine__isnull=False).values_list(
                    'virtual_machine_id', flat=True
                )
            ),
        },
    }


def _uncabled_interfaces():
    """{device_id: [interface names]} for enabled interfaces with no cable.
    LAGs are excluded as requested, along with the other interface types
    NetBox never allows a cable on (virtual, bridge, wireless) — those
    could never pass. Interfaces marked connected count as cabled."""
    result = defaultdict(list)
    interfaces = (
        Interface.objects.filter(enabled=True, cable__isnull=True, mark_connected=False)
        .exclude(type__in=NONCONNECTABLE_IFACE_TYPES)
        .values_list('device_id', 'name')
    )
    for device_id, name in interfaces:
        result[device_id].append(name)
    return result


def _duplicate_keys(ci_type, ci):
    name = (ci.name or '').strip().lower()
    serial = (getattr(ci, 'serial', '') or '').strip().lower()
    # Clusters are scoped generically; CachedScopeMixin keeps the resolved
    # Site in _site. Cluster Groups have no site at all.
    site_attr = '_site_id' if ci_type == ThreeCCITypeChoices.CI_CLUSTER else 'site_id'
    site_id = getattr(ci, site_attr, None)
    if serial:
        yield 'serial', ('serial', serial)
    if name:
        yield 'name', ('name', name)
        if site_id:
            yield 'name + site', ('name + site', name, site_id)


def _find_duplicates(ci_type, cis):
    """{pk: message} for every CI sharing a name, serial or name + site
    with another CI of the same class. CIs linked through any of those keys
    form one set; the oldest (lowest pk) is the original, so a set of N
    identical CIs counts N - 1 failures."""
    parent = {ci.pk: ci.pk for ci in cis}

    def find(pk):
        while parent[pk] != pk:
            parent[pk] = parent[parent[pk]]
            pk = parent[pk]
        return pk

    keys = defaultdict(list)
    for ci in cis:
        for label, key in _duplicate_keys(ci_type, ci):
            keys[(label, key)].append(ci.pk)

    shared = defaultdict(set)
    for (label, _key), pks in keys.items():
        if len(pks) < 2:
            continue
        for pk in pks:
            shared[pk].add(label)
            root_a, root_b = find(pks[0]), find(pk)
            if root_a != root_b:
                parent[max(root_a, root_b)] = min(root_a, root_b)

    groups = defaultdict(list)
    for pk in shared:
        groups[find(pk)].append(pk)

    by_pk = {ci.pk: ci for ci in cis}
    result = {}
    for members in groups.values():
        original = min(members)
        for pk in members:
            if pk != original:
                result[pk] = f'Duplicate of {by_pk[original]} (same {", ".join(sorted(shared[pk]))})'
    return result


def _relationship_health():
    """Pooled health of the plugin's own relationship chain (reported
    separately, not per CI class/tenant): orphans are Service Offerings
    with no Service and Services with no Portfolio (an Application Service
    can't lack its Service Offering — the database requires it); stale
    links are CI <-> Application Service links whose CI is stale."""
    orphan_failures = (
        ServiceOffering.objects.filter(service__isnull=True).count()
        + Service.objects.filter(service_portfolio__isnull=True).count()
    )
    orphan_total = ServiceOffering.objects.count() + Service.objects.count() + AppService.objects.count()

    stale_failures = stale_total = 0
    for ci_type, (info_model, fk_name) in INFO_MODELS.items():
        through = info_model.application_services.through
        stale_total += through.objects.count()
        if statuses := STALE_STATUSES.get(ci_type):
            stale_failures += through.objects.filter(
                **{f'{info_model._meta.model_name}__{fk_name}__status__in': statuses}
            ).count()

    return {
        SUB_ORPHAN: [orphan_failures, orphan_total],
        SUB_STALE: [stale_failures, stale_total],
    }


#
# The health check itself
#


def _ci_queryset(ci_type, rules):
    model = CI_MODELS[ci_type]
    prefetch = {
        f'{SERVICE_INFO_ACCESSOR}__application_services',
        f'{SERVICE_INFO_ACCESSOR}__support_group',
    }
    for rule in rules:
        key = rule.parameter
        if key.startswith(CUSTOM_FIELD_PREFIX):
            continue
        if key.startswith(SERVICE_INFO_PREFIX):
            prefetch.add(f'{SERVICE_INFO_ACCESSOR}__{key[len(SERVICE_INFO_PREFIX) :]}')
            continue
        try:
            field = model._meta.get_field(key)
        except FieldDoesNotExist:
            continue
        if field.is_relation:
            prefetch.add(key)
    return model.objects.prefetch_related(*sorted(prefetch)).order_by('pk')


def _evaluate_ci(ci_type, ci, rules_by_type, lifecycle, uncabled, duplicates, label_cache):
    """Return ({sub_metric: failed?} for every sub-metric this CI was
    evaluated for, {kpi: (sub_metrics, failure messages)} for each KPI it
    failed)."""
    evaluated = {}
    failed = {}

    # Completeness
    missing = {}
    for rule_type in (ThreeCRuleTypeChoices.TYPE_REQUIRED, ThreeCRuleTypeChoices.TYPE_RECOMMENDED):
        rules = rules_by_type[rule_type]
        if not rules:
            continue
        labels = [
            get_parameter_label(ci_type, rule.parameter, label_cache)
            for rule in rules
            if not rule_passes(rule, *resolve_parameter(ci, rule.parameter))
        ]
        evaluated[rule_type] = bool(labels)
        if labels:
            missing[rule_type] = sorted(set(labels), key=str.lower)
    if missing:
        failed[ThreeCKPIChoices.KPI_COMPLETENESS] = (
            list(missing),
            [f'Missing ({rule_type}): {", ".join(labels)}' for rule_type, labels in missing.items()],
        )

    # Correctness
    sub_metrics, messages = [], []
    if statuses := STALE_STATUSES.get(ci_type):
        is_stale = ci.status in statuses
        evaluated[SUB_STALE] = is_stale
        if is_stale:
            sub_metrics.append(SUB_STALE)
            messages.append(f'Stale: status {ci.get_status_display()}')

    orphan = []
    info = _service_info(ci)
    if info is None or not info.application_services.all():
        orphan.append('no Application Service')
    if lifecycle is not None:
        if ci_type == ThreeCCITypeChoices.CI_DEVICE and ci.device_type_id not in lifecycle['device_types']:
            orphan.append('no Hardware Lifecycle on its device type')
        if ci_type in lifecycle['contracts'] and ci.pk not in lifecycle['contracts'][ci_type]:
            orphan.append('no support contract assignment')
    if ci_type == ThreeCCITypeChoices.CI_DEVICE and (names := uncabled.get(ci.pk)):
        shown = ', '.join(names[:UNCABLED_INTERFACES_SHOWN])
        more = f' (+{len(names) - UNCABLED_INTERFACES_SHOWN} more)' if len(names) > UNCABLED_INTERFACES_SHOWN else ''
        orphan.append(f'enabled interfaces without a cable: {shown}{more}')
    evaluated[SUB_ORPHAN] = bool(orphan)
    if orphan:
        sub_metrics.append(SUB_ORPHAN)
        messages.append(f'Orphan: {"; ".join(orphan)}')

    duplicate = duplicates.get(ci.pk)
    evaluated[SUB_DUPLICATE] = bool(duplicate)
    if duplicate:
        sub_metrics.append(SUB_DUPLICATE)
        messages.append(duplicate)
    if messages:
        failed[ThreeCKPIChoices.KPI_CORRECTNESS] = (sub_metrics, messages)

    # Compliance
    rules = rules_by_type[ThreeCRuleTypeChoices.TYPE_COMPLIANCE]
    if rules:
        messages = []
        for rule in rules:
            display, tokens = resolve_parameter(ci, rule.parameter)
            if rule_passes(rule, display, tokens):
                continue
            expected = rule.get_condition_display()
            if rule.value:
                expected += f' {rule.value}'
            label = get_parameter_label(ci_type, rule.parameter, label_cache)
            messages.append(f'{rule.name}: {label} {expected} (actual: {", ".join(display) or "empty"})')
        evaluated[SUB_AUDIT] = bool(messages)
        if messages:
            failed[ThreeCKPIChoices.KPI_COMPLIANCE] = ([SUB_AUDIT], messages)

    return evaluated, failed


def run_health_check(logger=None):
    """Evaluate every in-scope CI, store a new ThreeCSnapshot with its
    findings, drop the previous snapshot's findings and prune snapshots
    past the retention period. Returns the new snapshot."""
    log = logger.info if logger else (lambda *args, **kwargs: None)
    settings = ThreeCSettings.load()

    rules = defaultdict(lambda: defaultdict(list))
    for rule in ThreeCRule.objects.filter(enabled=True):
        rules[rule.ci_type][rule.rule_type].append(rule)

    lifecycle = _lifecycle_lookups()
    if lifecycle is None:
        log('netbox-lifecycle is not installed: skipping the hardware lifecycle and support contract checks.')

    breakdown = {}
    findings = []
    ci_count = 0
    label_cache = {}

    for ci_type in CI_MODELS:
        rules_by_type = rules[ci_type]
        cis = list(_ci_queryset(ci_type, [r for rs in rules_by_type.values() for r in rs]))
        log(f'Evaluating {len(cis)} {CI_MODELS[ci_type]._meta.verbose_name_plural}')
        ci_count += len(cis)
        duplicates = _find_duplicates(ci_type, cis)
        uncabled = _uncabled_interfaces() if ci_type == ThreeCCITypeChoices.CI_DEVICE else {}

        for ci in cis:
            evaluated, failed = _evaluate_ci(ci_type, ci, rules_by_type, lifecycle, uncabled, duplicates, label_cache)

            tenant_id = getattr(ci, 'tenant_id', None)
            counts = breakdown.setdefault(ci_type, {}).setdefault(str(tenant_id or ''), {})
            for sub_metric, is_failure in evaluated.items():
                count = counts.setdefault(sub_metric, [0, 0])
                count[0] += int(is_failure)
                count[1] += 1

            if not failed:
                continue
            info = _service_info(ci)
            support_group = ', '.join(g.name for g in info.support_group.all()) if info else ''
            for kpi, (sub_metrics, messages) in failed.items():
                findings.append(
                    ThreeCFinding(
                        kpi=kpi,
                        ci_type=ci_type,
                        ci_id=ci.pk,
                        ci_name=str(ci)[:255],
                        tenant_id=tenant_id,
                        support_group=support_group[:500],
                        ci_last_updated=ci.last_updated,
                        sub_metrics=sub_metrics,
                        failures=messages,
                    )
                )

    scores = kpi_scores(aggregate_breakdown(breakdown))
    relationship = _relationship_health()
    relationship_score = health_score(
        sum(f for f, _t in relationship.values()),
        sum(t for _f, t in relationship.values()),
    )

    with transaction.atomic():
        snapshot = ThreeCSnapshot.objects.create(
            completeness=scores[ThreeCKPIChoices.KPI_COMPLETENESS],
            correctness=scores[ThreeCKPIChoices.KPI_CORRECTNESS],
            compliance=scores[ThreeCKPIChoices.KPI_COMPLIANCE],
            composite=scores['composite'],
            relationship_health=relationship_score,
            ci_count=ci_count,
            breakdown=breakdown,
            relationship_breakdown=relationship,
            lifecycle_checks=lifecycle is not None,
        )
        for finding in findings:
            finding.snapshot = snapshot
        ThreeCFinding.objects.bulk_create(findings, batch_size=1000)
        ThreeCFinding.objects.exclude(snapshot=snapshot).delete()
        cutoff = timezone.now() - timedelta(days=settings.snapshot_retention_days)
        ThreeCSnapshot.objects.filter(created__lt=cutoff).exclude(pk=snapshot.pk).delete()

    log(
        f'Snapshot #{snapshot.pk}: {ci_count} CIs, {len(findings)} findings; '
        f'completeness={snapshot.completeness}, correctness={snapshot.correctness}, '
        f'compliance={snapshot.compliance}, composite={snapshot.composite}, '
        f'relationship health={snapshot.relationship_health}'
    )
    return snapshot
