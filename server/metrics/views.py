import os
from posixpath import isabs
from re import M
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from custom_auth.permissions import IsAdmin
import requests

MAX_ALL_METRICS_LENGTH = 100
METRIC_COLLECT_JOB_ID = "collect_metrics_and_sent_to_db"

def call_from_metric_service(endpoint: str):
    try:
        metric_url = os.environ["METRIC_SERVER_URL"]
        response = requests.get(metric_url + endpoint)
        response.raise_for_status() # Raise an exception for 4xx/5xx status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from metric service: {e}")
        raise Exception("Failed to fetch data from metric service") from e

class GetAllContainerStatus(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self):
        data = call_from_metric_service('/status')
        return data
    
    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class GetRunningContainer(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self):
        data = call_from_metric_service('/status')
        return data
    
    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            running_containers = [key for key, value in data.items() if value == 'running']
            return Response(status=status.HTTP_200_OK, data=running_containers)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class GetChronosHealth(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self):
        data = call_from_metric_service('/health')
        return data
    
    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_200_OK, data={"error": str(e)})

class GetContainerMetadata(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self, container_name: str):
        data = call_from_metric_service('/container/' + container_name)
        return data
    
    def get(self, request: Request, container_name: str):
        try:
            data = self._call_from_metric_service(container_name)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class GetContainerRecentUsage(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self, container_name: str):
        data = call_from_metric_service('/usage/' + container_name)
        return data
    
    def get(self, request: Request, container_name: str):
        try:
            data = self._call_from_metric_service(container_name)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class GetContainerUsageHistory(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self, container_name: str):
        data = call_from_metric_service('/usage/' + container_name + '/all')
        return data
    
    def get(self, request: Request, container_name: str):
        try:
            data = self._call_from_metric_service(container_name)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class DisableMetricTask(APIView):
    # permission_classes = [IsAdmin]
    def _post_to_metric_service(self, job_id: str):
        try:
            metric_url = os.environ["METRIC_SERVER_URL"]
            response = requests.post(metric_url + '/poll/pause', json={"id": job_id})
            if response.status_code == 404:
                raise Exception(f"Job with ID '{job_id}' not found in the metric service.")
            response.raise_for_status()  # Raise for other 4xx/5xx errors
        except requests.exceptions.RequestException as e:
            print(f"Error posting data to metric service: {e}")
            raise Exception("Failed to post to metric service") from e

    def post(self, request: Request):
        try:
            job_id = request.data.get('job_id')
            if not job_id:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"error": "Missing 'job_id' in request data"}
                )
            self._post_to_metric_service(job_id)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": f"Job with ID '{job_id}' successfully paused"}
            )
        except Exception as e:
            if "not found" in str(e).lower():
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": str(e)}
                )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": str(e)}
            )

class EnableMetricCollection(APIView):
    # permission_classes = [IsAdmin]
    def _post_to_metric_service(self):
        try:
            metric_url = os.environ["METRIC_SERVER_URL"]
            response = requests.post(metric_url + '/poll/resume', json={"id": METRIC_COLLECT_JOB_ID})
            response.raise_for_status()  # Raise for other 4xx/5xx errors
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to post to metric service") from e
        
    def post(self, request: Request):
        try:
            self._post_to_metric_service()
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "Successfully enable metric collection"}
            )
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": str(e)}
            )

class DisableMetricCollection(APIView):
    # permission_classes = [IsAdmin]
    def _post_to_metric_service(self):
        try:
            metric_url = os.environ["METRIC_SERVER_URL"]
            response = requests.post(metric_url + '/poll/pause', json={"id": METRIC_COLLECT_JOB_ID})
            response.raise_for_status()  # Raise for other 4xx/5xx errors
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to post to metric service") from e
        
    def post(self, request: Request):
        try:
            self._post_to_metric_service()
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "Successfully disable metric collection"}
            )
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": str(e)}
            )
        
class GetMetricCollectionStatus(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self):
        data = call_from_metric_service('/job/' + METRIC_COLLECT_JOB_ID + '/status')
        return data
    
    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            res = data.get('status')[METRIC_COLLECT_JOB_ID]
            return Response(status=status.HTTP_200_OK, data={"status": res})
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class EnableMetricTask(APIView):
    # permission_classes = [IsAdmin]
    def _post_to_metric_service(self, job_id: str):
        try:
            metric_url = os.environ["METRIC_SERVER_URL"]
            response = requests.post(metric_url + '/poll/resume', json={"id": job_id})
            if response.status_code == 404:
                raise Exception(f"Job with ID '{job_id}' not found in the metric service.")
            response.raise_for_status()  # Raise for other 4xx/5xx errors
        except requests.exceptions.RequestException as e:
            print(f"Error posting data to metric service: {e}")
            raise Exception("Failed to post to metric service") from e

    def post(self, request: Request):
        try:
            job_id = request.data.get('job_id')
            if not job_id:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"error": "Missing 'job_id' in request data"}
                )
            self._post_to_metric_service(job_id)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": f"Job with ID '{job_id}' successfully resumed"}
            )
        except Exception as e:
            if "not found" in str(e).lower():
                return Response(
                    status=status.HTTP_404_NOT_FOUND,
                    data={"error": str(e)}
                )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"error": str(e)}
            )

class GetMetricTaskStatus(APIView):
    # permission_classes = [IsAdmin]
    def _call_from_metric_service(self, job_id: str):
        data = call_from_metric_service('/job/' + job_id + '/status')
        return data
    
    def get(self, request: Request, job_id: str):
        try:
            data = self._call_from_metric_service(job_id)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

class MetricViewAllRecent(APIView):
    # permission_classes = [IsAdmin]

    def _call_from_metric_service(self):
        data = call_from_metric_service('/usage')
        if(len(data) > MAX_ALL_METRICS_LENGTH):
            return data[:MAX_ALL_METRICS_LENGTH]
        return data

    def get(self, request: Request):
        try:
            data = self._call_from_metric_service()
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})