from django.db.models import Q

__all__ = ('tenant_offering_filter',)


def tenant_offering_filter(tenant):
    """Q object matching ServiceOfferings related to a Tenant, whether
    directly (ServiceOffering.tenant) or via its Tenant Group
    (ServiceOffering.tenant_group). Shared by the Reports/Table
    (views.TenantReportView) and Reports/Visual (views.OfferingsTreeView)
    views so this "direct-or-group" matching rule only lives in one place.

    Q(tenant_group=None) would match every offering with *no* group set
    (Django translates field=None to __isnull=True), not just ones tied to
    this specific ungrouped tenant — so the tenant_group half of the
    filter only gets added when there's actually a group to match against.
    """
    filters = Q(tenant=tenant)
    if tenant.group_id:
        filters |= Q(tenant_group=tenant.group_id)
    return filters
