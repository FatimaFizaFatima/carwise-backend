from sqlalchemy.exc import IntegrityError

from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.core.roles import BookingStatus, Role
from app.models.user_models import User
from app.models.workshop_review import WorkshopReview
from app.schema.workshop_review import ReviewCreateRequest, ReviewResponse
from app.service.workshop_service import get_approved_workshop


def _display_name(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name.strip()
    return f"{parts[0]} {parts[-1][0]}."


def _to_response(r: WorkshopReview, reviewer: User) -> ReviewResponse:
    return ReviewResponse(
        id=r.id, workshop_id=r.workshop_id, user_id=r.user_id, booking_id=r.booking_id,
        rating=r.rating, comment=r.comment, created_at=r.created_at,
        reviewer_name=_display_name(reviewer.full_name),
        reviewer_avatar_url=reviewer.avatar_url,
    )


async def create_review(current_user: User, workshop_id: int, data: ReviewCreateRequest) -> ReviewResponse:
    if current_user.role != Role.CUSTOMER:
        raise AppException("Only customers can submit reviews", status_code=403)

    async with UnitOfWork() as uow:
        workshop = await get_approved_workshop(uow, workshop_id)

        booking = await uow.bookings.get_by_id(data.booking_id)
        if booking is None or booking.user_id != current_user.id:
            raise AppException("Booking not found", status_code=404)
        if booking.workshop_id != workshop_id:
            raise AppException("This booking doesn't belong to this workshop", status_code=400)
        if booking.status != BookingStatus.COMPLETED:
            raise AppException("You can only review a completed booking", status_code=403)
        if await uow.workshop_reviews.exists_for_booking(data.booking_id):
            raise AppException("You've already reviewed this booking", status_code=409)

        review = WorkshopReview(
            workshop_id=workshop_id, user_id=current_user.id,
            booking_id=data.booking_id, rating=data.rating, comment=data.comment,
        )
        try:
            uow.workshop_reviews.add(review)
            await uow.session.flush()

            new_avg = await uow.workshop_reviews.get_average_rating(workshop_id)
            await uow.workshops.update(workshop, {"avg_rating": new_avg})

            await uow.commit()
        except IntegrityError:
            
            await uow.rollback()
            raise AppException("You've already reviewed this booking", status_code=409)
        return _to_response(review, current_user)


async def list_reviews(workshop_id: int, page: int, page_size: int) -> list[ReviewResponse]:
    async with UnitOfWork() as uow:
        await get_approved_workshop(uow, workshop_id)
        rows = await uow.workshop_reviews.get_by_workshop_with_reviewers(
            workshop_id, limit=page_size, offset=(page - 1) * page_size
        )
        return [_to_response(review, reviewer) for review, reviewer in rows]
