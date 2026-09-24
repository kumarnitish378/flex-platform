"""`/auth/*` and `/devices` (`api-spec.yaml`).

Routers parse, call a service, and return a schema — no business logic
(`coding-standards.md` §2 rule 1).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep, SettingsDep
from app.modules.auth.dependencies import public_route, self_service_route
from app.modules.auth.otp import OtpSender
from app.modules.auth.schemas import (
    DeviceRegister,
    Me,
    OtpRequest,
    OtpVerify,
    RefreshRequest,
    RoleEntry,
    TokenPair,
)
from app.modules.auth.service import AuthService

router = APIRouter(tags=["auth"])


def _service(
    request: Request, session: SessionDep, clock: ClockDep, settings: SettingsDep
) -> AuthService:
    sender: OtpSender = request.app.state.otp_sender
    return AuthService(session=session, clock=clock, settings=settings, otp_sender=sender)


@router.post(
    "/auth/otp/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request OTP",
    dependencies=[Depends(public_route())],
)
async def request_otp(
    body: OtpRequest,
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> Response:
    """202 whether or not the phone is known - see the note in api-spec.yaml."""
    await _service(request, session, clock, settings).request_otp(body.phone)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/auth/otp/verify",
    summary="Verify OTP and obtain tokens",
    dependencies=[Depends(public_route())],
)
async def verify_otp(
    body: OtpVerify,
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> TokenPair:
    device_info = request.headers.get("user-agent")
    tokens = await _service(request, session, clock, settings).verify_otp(
        body.phone, body.code, device_info
    )
    return TokenPair(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/auth/refresh",
    summary="Rotate the refresh token",
    dependencies=[Depends(public_route())],
)
async def refresh(
    body: RefreshRequest,
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> TokenPair:
    tokens = await _service(request, session, clock, settings).refresh(body.refresh_token)
    return TokenPair(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
    dependencies=[Depends(self_service_route())],
)
async def logout(
    body: RefreshRequest,
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> Response:
    await _service(request, session, clock, settings).logout(body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/auth/me",
    summary="Current user, roles and permissions",
    dependencies=[Depends(self_service_route())],
)
async def me(
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> Me:
    view = await _service(request, session, clock, settings).me(current_user.claims.user_id)
    return Me(
        user_id=view.user_id,
        name=view.name,
        phone=view.phone,
        roles=[
            RoleEntry(
                role=role.role,
                operator_id=role.operator_id,
                client_id=role.client_id,
                employee_id=role.employee_id,
                driver_id=role.driver_id,
                permissions=list(role.permissions),
            )
            for role in view.roles
        ],
    )


@router.post(
    "/devices",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Register or update a device push token",
    dependencies=[Depends(self_service_route())],
)
async def register_device(
    body: DeviceRegister,
    request: Request,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> Response:
    await _service(request, session, clock, settings).register_device(
        user_id=current_user.claims.user_id,
        platform=str(body.platform),
        push_token=body.push_token,
        app_version=body.app_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
