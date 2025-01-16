import os
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
import requests
from .models import ContainerMetrics

# Create your views here.
class MetricViewAllRecent(APIView):

    def _call_from_metric_service(self):
        try:
            metric_url = os.environ["METRIC_SERVER_URL"]
            response = requests.get(metric_url + '/all')
            response.raise_for_status() # Raise an exception for 4xx/5xx status codes
            data = response.json()
            print("Data fetched from metric service")
            return data[:10]  # Return the first 10 metrics
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from metric service: {e}")
            raise Exception("Failed to fetch data from metric service") from e

    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})