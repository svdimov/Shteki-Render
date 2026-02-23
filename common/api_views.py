from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.shortcuts import get_object_or_404


from events.models import Event
from common.models import EventParticipation
from events.choices import StatusChoice

class EventStatusAPI(APIView):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        user = request.user

        status_value = request.data.get('status')
        valid_statuses = [choice[0] for choice in StatusChoice.choices]

        if status_value not in valid_statuses:
            return Response({'error': 'Invalid status'}, status=http_status.HTTP_400_BAD_REQUEST)

        participation, created = EventParticipation.objects.update_or_create(
            event=event,
            user=user,
            defaults={'status': status_value}
        )

        return Response({'message': 'Status updated'}, status=http_status.HTTP_200_OK)



