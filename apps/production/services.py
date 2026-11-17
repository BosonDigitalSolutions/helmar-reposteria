"""Fichas de cocina y el estado del pedido que depende de ellas."""

from datetime import timedelta

from django.utils import timezone

from apps.production.models import ProductionJob


def prep_date(line, event_date):
    days = line.product.lead_time_days if line.product_id else 0
    return event_date - timedelta(days=days)


def create_jobs(order):
    event_date = timezone.localtime(order.event_at).date()
    jobs = []
    for line in order.lines.select_related("product"):
        jobs.append(
            ProductionJob(
                order=order,
                order_line=line,
                summary=line.description,
                scheduled_date=prep_date(line, event_date),
            )
        )
    ProductionJob.objects.bulk_create(jobs)
    return jobs


def refresh_open_prep_dates(order):
    event_date = timezone.localtime(order.event_at).date()
    for job in order.jobs.select_related("order_line__product"):
        if job.status != ProductionJob.Status.TODO:
            continue
        job.scheduled_date = prep_date(job.order_line, event_date)
        job.save(update_fields=["scheduled_date"])


def sync_order_status(order):
    from apps.orders.models import Order

    if order.status in {Order.Status.DELIVERED, Order.Status.CANCELLED}:
        return order
    statuses = set(order.jobs.values_list("status", flat=True))
    if not statuses:
        return order
    if statuses == {ProductionJob.Status.READY}:
        new_status = Order.Status.READY
    elif statuses == {ProductionJob.Status.TODO}:
        new_status = Order.Status.CONFIRMED
    else:
        new_status = Order.Status.IN_PRODUCTION
    if new_status != order.status:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
    return order
