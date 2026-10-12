from datetime import timedelta

from core.choices import JobStatusChoices
from django.db import transaction
from django.utils import timezone
from django_pglocks import advisory_lock
from netbox.jobs import JobRunner

from .models import ThreeCSettings
from .three_c import run_health_check

__all__ = (
    'ThreeCHealthJob',
    'ensure_scheduled',
)

# Minutes. The scheduled run re-enqueues itself this far after its own
# scheduled time (see JobRunner.handle()), so it stays on the same
# time of day; "Run now" jobs are enqueued without an interval.
SCHEDULE_INTERVAL = 24 * 60


class ThreeCHealthJob(JobRunner):
    class Meta:
        name = '3C Health Calculation'

    def run(self, *args, **kwargs):
        run_health_check(logger=self.logger)


def next_run_at(job_time, now=None):
    now = timezone.localtime(now or timezone.now())
    run_at = now.replace(hour=job_time.hour, minute=job_time.minute, second=0, microsecond=0)
    if run_at <= now:
        run_at += timedelta(days=1)
    return run_at


def ensure_scheduled(settings=None):
    """Make sure exactly one daily 3C job is scheduled, at ThreeCSettings'
    job_time. Idempotent and cheap, so it's simply called whenever the
    report is viewed or the settings are saved — this is what creates the
    schedule in the first place, and what moves it after job_time changes.

    NetBox's own JobRunner.enqueue_once() isn't used: it treats a
    *running* job as the current schedule and would delete it whenever the
    requested time differs. A running scheduled job is left alone here —
    JobRunner.handle() enqueues its successor once it finishes.
    """
    settings = settings or ThreeCSettings.load()
    job_time = settings.job_time.replace(second=0, microsecond=0)

    with transaction.atomic(), advisory_lock('service_specification_3c_schedule'):
        jobs = ThreeCHealthJob.get_jobs().filter(
            interval=SCHEDULE_INTERVAL,
            status__in=JobStatusChoices.ENQUEUED_STATE_CHOICES,
        )
        current = None
        for job in jobs:
            if job.status == JobStatusChoices.STATUS_RUNNING:
                return job
            scheduled_time = job.scheduled and timezone.localtime(job.scheduled).time().replace(second=0, microsecond=0)
            if current is None and scheduled_time == job_time:
                current = job
            else:
                job.delete()
        if current:
            return current
        return ThreeCHealthJob.enqueue(schedule_at=next_run_at(job_time), interval=SCHEDULE_INTERVAL)
