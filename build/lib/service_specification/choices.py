from utilities.choices import ChoiceSet


class TimeUnitChoices(ChoiceSet):
    UNIT_SECONDS = 'seconds'
    UNIT_MINUTES = 'minutes'
    UNIT_HOURS = 'hours'
    UNIT_DAYS = 'days'
    UNIT_WEEKS = 'weeks'
    UNIT_MONTHS = 'months'
    UNIT_YEARS = 'years'

    CHOICES = (
        (UNIT_SECONDS, 'Seconds'),
        (UNIT_MINUTES, 'Minutes'),
        (UNIT_HOURS, 'Hours'),
        (UNIT_DAYS, 'Days'),
        (UNIT_WEEKS, 'Weeks'),
        (UNIT_MONTHS, 'Months'),
        (UNIT_YEARS, 'Years'),
    )


class RateCardIntervalChoices(ChoiceSet):
    INTERVAL_MONTHLY = 'monthly'
    INTERVAL_ONE_TIME = 'one-time'
    INTERVAL_OTHERS = 'others'

    CHOICES = (
        (INTERVAL_MONTHLY, 'Monthly'),
        (INTERVAL_ONE_TIME, 'One time cost'),
        (INTERVAL_OTHERS, 'Others'),
    )


#
# 3C (CMDB health) choices
#


class ThreeCCITypeChoices(ChoiceSet):
    # Values are the core models' own model_name, so they double as
    # ContentType lookups / URL names without a separate mapping table.
    CI_DEVICE = 'device'
    CI_VIRTUAL_MACHINE = 'virtualmachine'
    CI_CLUSTER = 'cluster'
    CI_CLUSTER_GROUP = 'clustergroup'

    CHOICES = (
        (CI_DEVICE, 'Device'),
        (CI_VIRTUAL_MACHINE, 'Virtual Machine'),
        (CI_CLUSTER, 'Cluster'),
        (CI_CLUSTER_GROUP, 'Cluster Group'),
    )


class ThreeCRuleTypeChoices(ChoiceSet):
    TYPE_REQUIRED = 'required'
    TYPE_RECOMMENDED = 'recommended'
    TYPE_COMPLIANCE = 'compliance'

    CHOICES = (
        (TYPE_REQUIRED, 'Completeness: Required', 'red'),
        (TYPE_RECOMMENDED, 'Completeness: Recommended', 'orange'),
        (TYPE_COMPLIANCE, 'Compliance', 'blue'),
    )


class ThreeCConditionChoices(ChoiceSet):
    CONDITION_NOT_EMPTY = 'not_empty'
    CONDITION_EMPTY = 'empty'
    CONDITION_EQUALS = 'equals'
    CONDITION_NOT_EQUALS = 'not_equals'
    CONDITION_IN = 'in'
    CONDITION_NOT_IN = 'not_in'
    CONDITION_REGEX = 'regex'

    CHOICES = (
        (CONDITION_NOT_EMPTY, 'is not empty'),
        (CONDITION_EMPTY, 'is empty'),
        (CONDITION_EQUALS, 'equals'),
        (CONDITION_NOT_EQUALS, 'does not equal'),
        (CONDITION_IN, 'is one of'),
        (CONDITION_NOT_IN, 'is not one of'),
        (CONDITION_REGEX, 'matches regex'),
    )

    # Conditions that compare against the rule's `value` (the rest ignore it).
    VALUE_REQUIRED = (
        CONDITION_EQUALS,
        CONDITION_NOT_EQUALS,
        CONDITION_IN,
        CONDITION_NOT_IN,
        CONDITION_REGEX,
    )


class ThreeCKPIChoices(ChoiceSet):
    KPI_COMPLETENESS = 'completeness'
    KPI_CORRECTNESS = 'correctness'
    KPI_COMPLIANCE = 'compliance'

    CHOICES = (
        (KPI_COMPLETENESS, 'Completeness', 'blue'),
        (KPI_CORRECTNESS, 'Correctness', 'purple'),
        (KPI_COMPLIANCE, 'Compliance', 'teal'),
    )
