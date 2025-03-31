import logging

import requests
from custom_auth.permissions import IsAdmin
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from server.settings import METRIC_SERVER_URL

MAX_ALL_METRICS_LENGTH = 100
METRIC_COLLECT_JOB_ID = "collect_metrics_and_sent_to_db"


logger = logging.getLogger(__name__)


class MetricServerAPI:
    def get_from_metric_service(self, endpoint: str):
        try:
            logger.info(f"Fetching data from metric service: {endpoint}")
            metric_url = METRIC_SERVER_URL
            response = requests.get(metric_url + endpoint)
            response.raise_for_status()  # Raise an exception for 4xx/5xx status codes
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from metric service: {e}")
            raise Exception("Failed to fetch data from metric service") from e

    def post_from_metric_service(self, endpoint: str, data: dict):
        try:
            metric_url = METRIC_SERVER_URL
            response = requests.post(metric_url + endpoint, json=data)
            response.raise_for_status()  # Raise an exception for 4xx/5xx status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting data from metric service: {e}")
            raise Exception("Failed to fetch data from metric service") from e

    def post_job_to_metric_service(self, endpoint: str, job_id: str):
        try:
            metric_url = METRIC_SERVER_URL
            response = requests.post(metric_url + endpoint, json={"id": job_id})
            if response.status_code == 404:
                raise Exception(
                    f"Job with ID '{job_id}' not found in the metric service."
                )
            response.raise_for_status()  # Raise for other 4xx/5xx errors
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting data to metric service: {e}")
            raise Exception("Failed to post to metric service") from e


class GetAllContainerStatus(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request):
        try:
            data = self.get_from_metric_service("/status")
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetRunningContainer(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request):
        try:
            data = self.get_from_metric_service("/status")
            running_containers = [
                key for key, value in data.items() if value == "running"
            ]
            return Response(status=status.HTTP_200_OK, data=running_containers)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetChronosHealth(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request):
        try:
            data = self.get_from_metric_service("/health")
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})


class GetContainerMetadata(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request, container_name: str):
        try:
            data = self.get_from_metric_service("/container/" + container_name)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetContainerRecentUsage(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request, container_name: str):
        try:
            data = self.get_from_metric_service("/usage/" + container_name)
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetContainerUsageHistory(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request, container_name: str):
        try:
            data = self.get_from_metric_service("/usage/" + container_name + "/all")
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class DisableMetricTask(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def post(self, request: Request):
        try:
            job_id = request.data.get("job_id")
            if not job_id:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"error": "Missing 'job_id' in request data"},
                )
            self.post_job_to_metric_service("/poll/pause", job_id)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": f"Job with ID '{job_id}' successfully paused"},
            )
        except Exception as e:
            if "not found" in str(e).lower():
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": str(e)}
                )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class EnableMetricCollection(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def post(self, request: Request):
        try:
            self.post_job_to_metric_service("/poll/resume", METRIC_COLLECT_JOB_ID)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "Successfully enable metric collection"},
            )
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class DisableMetricCollection(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def post(self, request: Request):
        try:
            self.post_job_to_metric_service("/poll/pause", METRIC_COLLECT_JOB_ID)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "Successfully disable metric collection"},
            )
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetMetricCollectionStatus(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request):
        try:
            data = self.get_from_metric_service(
                "/job/" + METRIC_COLLECT_JOB_ID + "/status"
            )
            res = data.get("status")[METRIC_COLLECT_JOB_ID]
            return Response(status=status.HTTP_200_OK, data={"status": res})
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class EnableMetricTask(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def post(self, request: Request):
        try:
            job_id = request.data.get("job_id")
            if not job_id:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"error": "Missing 'job_id' in request data"},
                )
            self.post_job_to_metric_service("/poll/resume", job_id)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": f"Job with ID '{job_id}' successfully resumed"},
            )
        except Exception as e:
            if "not found" in str(e).lower():
                return Response(
                    status=status.HTTP_404_NOT_FOUND, data={"error": str(e)}
                )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class GetMetricTaskStatus(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request, job_id: str):
        try:
            data = self.get_from_metric_service("/job/" + job_id + "/status")
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )


class MetricViewAllRecent(APIView, MetricServerAPI):
    permission_classes = [IsAdmin]

    def get(self, request: Request):
        try:
            data = self.get_from_metric_service("/usage")
            if len(data) > MAX_ALL_METRICS_LENGTH:
                data = data[:MAX_ALL_METRICS_LENGTH]
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)}
            )
