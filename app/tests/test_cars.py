from app.core.roles import Role, AccountStatus
from app.tests.conftest import car_payload


# ---------- Authentication ----------

async def test_create_car_requires_authentication(client):
    resp = await client.post("/cars", json=car_payload())
    assert resp.status_code == 401


async def test_list_cars_rejects_invalid_token(client):
    resp = await client.get("/cars", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


# ---------- Create ----------

async def test_customer_can_create_own_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)

    resp = await client.post("/cars", json=car_payload(), headers=headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["registration_no"].startswith("REG-")
    created_car_ids.append(body["id"])


async def test_create_car_duplicate_registration_no_is_rejected(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    payload = car_payload()

    first = await client.post("/cars", json=payload, headers=headers)
    assert first.status_code == 201
    created_car_ids.append(first.json()["id"])

    duplicate = await client.post("/cars", json=payload, headers=headers)
    assert duplicate.status_code == 409


async def test_create_car_invalid_model_year_is_rejected(client, user_factory):
    _, headers = await user_factory(role=Role.CUSTOMER)

    resp = await client.post("/cars", json=car_payload(model_year=1899), headers=headers)

    assert resp.status_code == 422


async def test_create_car_future_registration_date_is_rejected(client, user_factory):
    _, headers = await user_factory(role=Role.CUSTOMER)

    resp = await client.post("/cars", json=car_payload(registration_date="2099-01-01"), headers=headers)

    assert resp.status_code == 422


async def test_create_car_missing_required_field_is_rejected(client, user_factory):
    _, headers = await user_factory(role=Role.CUSTOMER)
    payload = car_payload()
    del payload["make"]

    resp = await client.post("/cars", json=payload, headers=headers)

    assert resp.status_code == 422


async def test_workshop_staff_cannot_create_car(client, user_factory):
    _, headers = await user_factory(role=Role.WORKSHOP_STAFF)

    resp = await client.post("/cars", json=car_payload(), headers=headers)

    assert resp.status_code == 403


async def test_customer_cannot_assign_car_to_another_user(client, user_factory):
    _, headers = await user_factory(role=Role.CUSTOMER)
    other_user, _ = await user_factory(role=Role.CUSTOMER)

    resp = await client.post("/cars", json=car_payload(user_id=other_user.id), headers=headers)

    assert resp.status_code == 403


async def test_admin_can_create_car_for_another_user(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, admin_headers = await user_factory(role=Role.ADMIN)
    customer, _ = await user_factory(role=Role.CUSTOMER)

    resp = await client.post("/cars", json=car_payload(user_id=customer.id), headers=admin_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == customer.id
    created_car_ids.append(body["id"])


# ---------- Read ----------

async def test_customer_can_get_own_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    create_resp = await client.post("/cars", json=car_payload(), headers=headers)
    car_id = create_resp.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.get(f"/cars/{car_id}", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == car_id


async def test_customer_cannot_get_other_customers_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, owner_headers = await user_factory(role=Role.CUSTOMER)
    _, other_headers = await user_factory(role=Role.CUSTOMER)
    create_resp = await client.post("/cars", json=car_payload(), headers=owner_headers)
    car_id = create_resp.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.get(f"/cars/{car_id}", headers=other_headers)

    assert resp.status_code == 403


async def test_get_nonexistent_car_returns_404(client, user_factory):
    _, headers = await user_factory(role=Role.CUSTOMER)

    resp = await client.get("/cars/999999999", headers=headers)

    assert resp.status_code == 404


async def test_customer_list_cars_only_returns_own(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers_a = await user_factory(role=Role.CUSTOMER)
    _, headers_b = await user_factory(role=Role.CUSTOMER)

    car_a = await client.post("/cars", json=car_payload(), headers=headers_a)
    car_b = await client.post("/cars", json=car_payload(), headers=headers_b)
    created_car_ids += [car_a.json()["id"], car_b.json()["id"]]

    resp = await client.get("/cars", headers=headers_a)

    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert car_a.json()["id"] in ids
    assert car_b.json()["id"] not in ids


async def test_staff_list_cars_requires_target_user_id(client, user_factory):
    _, headers = await user_factory(role=Role.WORKSHOP_STAFF)

    resp = await client.get("/cars", headers=headers)

    assert resp.status_code == 400


async def test_staff_list_cars_with_target_user_id(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    customer, customer_headers = await user_factory(role=Role.CUSTOMER)
    _, staff_headers = await user_factory(role=Role.WORKSHOP_STAFF)
    car = await client.post("/cars", json=car_payload(), headers=customer_headers)
    created_car_ids.append(car.json()["id"])

    resp = await client.get(f"/cars?target_user_id={customer.id}", headers=staff_headers)

    assert resp.status_code == 200
    assert any(c["id"] == car.json()["id"] for c in resp.json())


# ---------- Update ----------

async def test_customer_can_update_own_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    car = await client.post("/cars", json=car_payload(), headers=headers)
    car_id = car.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.put(f"/cars/{car_id}", json={"owner_name": "Updated Name"}, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["owner_name"] == "Updated Name"


async def test_customer_cannot_update_other_customers_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, owner_headers = await user_factory(role=Role.CUSTOMER)
    _, other_headers = await user_factory(role=Role.CUSTOMER)
    car = await client.post("/cars", json=car_payload(), headers=owner_headers)
    car_id = car.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.put(f"/cars/{car_id}", json={"owner_name": "Hijacked"}, headers=other_headers)

    assert resp.status_code == 403


# ---------- Delete + soft-delete regression ----------

async def test_delete_car_is_soft_delete(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    car = await client.post("/cars", json=car_payload(), headers=headers)
    car_id = car.json()["id"]
    created_car_ids.append(car_id)

    delete_resp = await client.delete(f"/cars/{car_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/cars/{car_id}", headers=headers)
    assert get_resp.status_code == 404  # invisible to normal reads, but still in the DB


async def test_workshop_staff_cannot_delete_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, owner_headers = await user_factory(role=Role.CUSTOMER)
    _, staff_headers = await user_factory(role=Role.WORKSHOP_STAFF)
    car = await client.post("/cars", json=car_payload(), headers=owner_headers)
    car_id = car.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.delete(f"/cars/{car_id}", headers=staff_headers)

    assert resp.status_code == 403


async def test_registration_no_reusable_after_soft_delete(client, user_factory, db_cleanup):
    """Regression test for the soft-delete duplicate-check bug."""
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    payload = car_payload()

    first = await client.post("/cars", json=payload, headers=headers)
    assert first.status_code == 201
    first_id = first.json()["id"]

    delete_resp = await client.delete(f"/cars/{first_id}", headers=headers)
    assert delete_resp.status_code == 204

    second = await client.post("/cars", json=payload, headers=headers)
    assert second.status_code == 201  # previously failed with 409
    created_car_ids += [first_id, second.json()["id"]]

    # But two ACTIVE cars still can't share the same registration/engine no
    third = await client.post("/cars", json=payload, headers=headers)
    assert third.status_code == 409


async def test_engine_number_reusable_after_soft_delete(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, headers = await user_factory(role=Role.CUSTOMER)
    shared_engine_no = car_payload()["engine_number"]

    first = await client.post("/cars", json=car_payload(engine_number=shared_engine_no), headers=headers)
    assert first.status_code == 201
    first_id = first.json()["id"]

    await client.delete(f"/cars/{first_id}", headers=headers)

    second = await client.post("/cars", json=car_payload(engine_number=shared_engine_no), headers=headers)
    assert second.status_code == 201
    created_car_ids += [first_id, second.json()["id"]]


# ---------- Staff/Admin association ----------

async def test_staff_can_associate_car_to_customer(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, staff_headers = await user_factory(role=Role.WORKSHOP_STAFF)
    _, admin_headers = await user_factory(role=Role.ADMIN)
    customer, _ = await user_factory(role=Role.CUSTOMER)
    # Admin creates an unowned/walk-in car for staff to then associate
    car = await client.post("/cars", json=car_payload(), headers=admin_headers)
    car_id = car.json()["id"]
    created_car_ids.append(car_id)

    resp = await client.post(f"/cars/{car_id}/associate", json={"user_id": customer.id}, headers=staff_headers)

    assert resp.status_code == 200
    assert resp.json()["user_id"] == customer.id


async def test_customer_cannot_associate_car(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, admin_headers = await user_factory(role=Role.ADMIN)
    customer, customer_headers = await user_factory(role=Role.CUSTOMER)
    other_customer, _ = await user_factory(role=Role.CUSTOMER)
    car = await client.post("/cars", json=car_payload(), headers=admin_headers)
    created_car_ids.append(car.json()["id"])

    resp = await client.post(
        f"/cars/{car.json()['id']}/associate",
        json={"user_id": other_customer.id},
        headers=customer_headers,
    )

    assert resp.status_code == 403


async def test_associate_to_nonexistent_user_returns_404(client, user_factory, db_cleanup):
    created_car_ids, _ = db_cleanup
    _, staff_headers = await user_factory(role=Role.WORKSHOP_STAFF)
    _, admin_headers = await user_factory(role=Role.ADMIN)
    car = await client.post("/cars", json=car_payload(), headers=admin_headers)
    created_car_ids.append(car.json()["id"])

    resp = await client.post(
        f"/cars/{car.json()['id']}/associate",
        json={"user_id": 999999999},
        headers=staff_headers,
    )

    assert resp.status_code == 404


# ---------- Account status ----------

async def test_pending_approval_staff_cannot_access_cars(client, user_factory):
    _, headers = await user_factory(role=Role.WORKSHOP_STAFF, status=AccountStatus.PENDING_APPROVAL)

    resp = await client.get("/cars?target_user_id=1", headers=headers)

    assert resp.status_code == 403