"""Router for DataSource management API."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.deps import CurrentUser, get_current_user, get_db_session, org_guard, require_roles
from apps.core.schemas.datasource import (
    ConnectivityCheckOut,
    DataSourceCreate,
    DataSourceOut,
    DataSourceTestCheck,
    DataSourceUpdate,
)

from .service import DataSourceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orgs/{org_id}/datasources", tags=["datasources"])


# ===== Helper Dependencies =====


def get_datasource_service(
    db: AsyncSession = Depends(get_db_session),
) -> DataSourceService:
    """Get DataSource service instance."""
    return DataSourceService(db)


def require_data_steward_or_admin():
    """Require either DATA_STEWARD or ORG_ADMIN role."""
    return require_roles("DATA_STEWARD", "ORG_ADMIN")


# ===== API Endpoints =====


@router.post(
    "/",
    response_model=DataSourceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def create_datasource(
    org_id: UUID,
    payload: DataSourceCreate,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DataSourceOut:
    """
    Create a new DataSource.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        payload: DataSource creation payload.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        Created DataSource (public view, no secrets).

    Raises:
        HTTPException: 400 if validation fails or name conflicts.
    """
    try:
        datasource = await service.create_datasource(org_id, payload)
        return DataSourceOut.model_validate(datasource)
    except ValueError as e:
        logger.warning(f"DataSource creation failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error creating DataSource: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create DataSource",
        ) from e


@router.get(
    "/",
    response_model=list[DataSourceOut],
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def list_datasources(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[DataSourceOut]:
    """
    List all DataSources for the organization.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        List of DataSources (public view, no secrets).
    """
    try:
        datasources = await service.list_datasources(org_id, skip, limit)
        return [DataSourceOut.model_validate(ds) for ds in datasources]
    except Exception as e:
        logger.error(f"Error listing DataSources for org {org_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list DataSources",
        ) from e


@router.get(
    "/{ds_id}",
    response_model=DataSourceOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def get_datasource(
    org_id: UUID,
    ds_id: UUID,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DataSourceOut:
    """
    Get DataSource details.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        ds_id: DataSource ID from path.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        DataSource details (public view, no secrets).

    Raises:
        HTTPException: 404 if not found.
    """
    datasource = await service.get_datasource(org_id, ds_id)
    if not datasource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DataSource not found",
        )
    return DataSourceOut.model_validate(datasource)


@router.put(
    "/{ds_id}",
    response_model=DataSourceOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def update_datasource(
    org_id: UUID,
    ds_id: UUID,
    payload: DataSourceUpdate,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DataSourceOut:
    """
    Update a DataSource.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        ds_id: DataSource ID from path.
        payload: Update payload.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        Updated DataSource (public view, no secrets).

    Raises:
        HTTPException: 400 if validation fails, 404 if not found.
    """
    try:
        datasource = await service.update_datasource(org_id, ds_id, payload)
        return DataSourceOut.model_validate(datasource)
    except ValueError as e:
        logger.warning(f"DataSource update failed for {ds_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error updating DataSource {ds_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update DataSource",
        ) from e


@router.delete(
    "/{ds_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def delete_datasource(
    org_id: UUID,
    ds_id: UUID,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Delete a DataSource.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        ds_id: DataSource ID from path.
        service: DataSource service.
        current_user: Current authenticated user.

    Raises:
        HTTPException: 404 if not found.
    """
    try:
        await service.delete_datasource(org_id, ds_id)
    except ValueError as e:
        logger.warning(f"DataSource deletion failed for {ds_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error deleting DataSource {ds_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete DataSource",
        ) from e


@router.post(
    "/{ds_id}/check",
    response_model=ConnectivityCheckOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def check_datasource_connectivity(
    org_id: UUID,
    ds_id: UUID,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ConnectivityCheckOut:
    """
    Test connectivity for a saved DataSource.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        ds_id: DataSource ID from path.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        Connectivity check result.

    Raises:
        HTTPException: 404 if not found.
    """
    ok, details = await service.check_connectivity(org_id, ds_id)
    if not ok and "not found" in details.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=details,
        )
    return ConnectivityCheckOut(ok=ok, details=details)


@router.post(
    "/check",
    response_model=ConnectivityCheckOut,
    dependencies=[Depends(org_guard()), Depends(require_data_steward_or_admin())],
)
async def check_draft_connectivity(
    org_id: UUID,
    payload: DataSourceTestCheck,
    service: DataSourceService = Depends(get_datasource_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ConnectivityCheckOut:
    """
    Test connectivity for a draft DataSource (without saving).

    Useful for validating connection settings in the creation form.

    Requires: ORG_ADMIN or DATA_STEWARD role.

    Args:
        org_id: Organization ID from path.
        payload: Test check payload.
        service: DataSource service.
        current_user: Current authenticated user.

    Returns:
        Connectivity check result.
    """
    ok, details = await service.check_connectivity_draft(payload)
    return ConnectivityCheckOut(ok=ok, details=details)
