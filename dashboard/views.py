from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from accounts.permissions import require_permission
from core.responses import success
from core.schema import ERRORS, envelope

from . import cache, services


class SummarySerializer(serializers.Serializer):
    totalRequests = serializers.IntegerField()
    openRequests = serializers.IntegerField()
    inProgressRequests = serializers.IntegerField()
    resolvedRequests = serializers.IntegerField()
    highPriorityRequests = serializers.IntegerField()
    overdueRequests = serializers.IntegerField()
    lastOverdueCheckAt = serializers.DateTimeField(allow_null=True)


class SummaryView(APIView):
    permission_classes = [require_permission("dashboard.read")]

    @extend_schema(tags=["Dashboard"], summary="Dashboard summary (cached ~60s in Redis)",
                   responses={200: envelope("DashboardSummaryEnvelope", SummarySerializer), 401: ERRORS[401], 403: ERRORS[403]})
    def get(self, request):
        summary = cache.get()
        hit = summary is not None
        if not hit:
            summary = services.build_summary()
            cache.put(summary)
        last_check = services.last_overdue_check_at()
        data = {**summary, "lastOverdueCheckAt": SummarySerializer().fields["lastOverdueCheckAt"].to_representation(last_check) if last_check else None}
        return success("Dashboard summary retrieved", data, headers={"X-Cache": "HIT" if hit else "MISS"})
