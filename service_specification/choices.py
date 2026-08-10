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
