import strawberry
import strawberry_django
from netbox.graphql.types import OrganizationalObjectType, PrimaryObjectType

from . import models

__all__ = ('schema',)


#
# Support / lookup types
#


@strawberry_django.type(models.Lifecycle, fields='__all__', pagination=True)
class LifecycleType(OrganizationalObjectType):
    # Explicit override, exactly like NetBox core's own TagType does for
    # Tag.color: strawberry-django's auto field-type resolution doesn't
    # recognize utilities.fields.ColorField (a CharField subclass) and
    # raises NotImplementedError building the schema without this.
    color: str


@strawberry_django.type(models.SLA, fields='__all__', pagination=True)
class SLAType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.OperationTime, fields='__all__', pagination=True)
class OperationTimeType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.Availability, fields='__all__', pagination=True)
class AvailabilityType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.Criticality, fields='__all__', pagination=True)
class CriticalityType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.Environment, fields='__all__', pagination=True)
class EnvironmentType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.MTAT, fields='__all__', pagination=True)
class MTATType(OrganizationalObjectType):
    pass


@strawberry_django.type(models.CIFunction, fields='__all__', pagination=True)
class CIFunctionType(OrganizationalObjectType):
    pass


#
# Core Service Specification types
#


@strawberry_django.type(models.Contract, fields='__all__', pagination=True)
class ContractType(PrimaryObjectType):
    # Computed property (models.py), not a real column — needs an explicit
    # annotated field, same as LifecycleType's `color: str` above (which
    # instead works around a field-type strawberry-django can't resolve on
    # its own; this is the same mechanism for a field that isn't there at
    # all until getattr() is called on the instance).
    status: str


@strawberry_django.type(models.ContractRateCard, fields='__all__', pagination=True)
class ContractRateCardType(PrimaryObjectType):
    total_costs: str


@strawberry_django.type(models.Portfolio, fields='__all__', pagination=True)
class PortfolioType(PrimaryObjectType):
    pass


@strawberry_django.type(models.Service, fields='__all__', pagination=True)
class ServiceType(PrimaryObjectType):
    pass


@strawberry_django.type(models.ServiceOffering, fields='__all__', pagination=True)
class ServiceOfferingType(PrimaryObjectType):
    pass


@strawberry_django.type(models.AppService, fields='__all__', pagination=True)
class AppServiceType(PrimaryObjectType):
    pass


@strawberry.type(name='Query')
class ServiceSpecificationQuery:
    contract: ContractType = strawberry_django.field()
    contract_list: list[ContractType] = strawberry_django.field()

    contract_rate_card: ContractRateCardType = strawberry_django.field()
    contract_rate_card_list: list[ContractRateCardType] = strawberry_django.field()

    portfolio: PortfolioType = strawberry_django.field()
    portfolio_list: list[PortfolioType] = strawberry_django.field()

    service: ServiceType = strawberry_django.field()
    service_list: list[ServiceType] = strawberry_django.field()

    service_offering: ServiceOfferingType = strawberry_django.field()
    service_offering_list: list[ServiceOfferingType] = strawberry_django.field()

    app_service: AppServiceType = strawberry_django.field()
    app_service_list: list[AppServiceType] = strawberry_django.field()

    lifecycle: LifecycleType = strawberry_django.field()
    lifecycle_list: list[LifecycleType] = strawberry_django.field()

    sla: SLAType = strawberry_django.field()
    sla_list: list[SLAType] = strawberry_django.field()

    operation_time: OperationTimeType = strawberry_django.field()
    operation_time_list: list[OperationTimeType] = strawberry_django.field()

    availability: AvailabilityType = strawberry_django.field()
    availability_list: list[AvailabilityType] = strawberry_django.field()

    criticality: CriticalityType = strawberry_django.field()
    criticality_list: list[CriticalityType] = strawberry_django.field()

    environment: EnvironmentType = strawberry_django.field()
    environment_list: list[EnvironmentType] = strawberry_django.field()

    mtat: MTATType = strawberry_django.field()
    mtat_list: list[MTATType] = strawberry_django.field()

    ci_function: CIFunctionType = strawberry_django.field()
    ci_function_list: list[CIFunctionType] = strawberry_django.field()


schema = [ServiceSpecificationQuery]
