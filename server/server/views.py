from rest_framework.views import APIView
from rest_framework.response import Response
from custom_auth.permissions import IsAdmin
from members.permissions import IsApiKey
from django.core.management import call_command
import io
import sys
from typing import List, Dict


class ManagementCommandView(APIView):
    permission_classes = (IsAdmin|IsApiKey,)

    ALLOWED_COMMANDS: List[Dict] = [
        {
            'name': 'list_users',
            'description': 'Lists all users in the system'
        },
        {
          'name': 'update_github_stats',
          'description': 'Updates GitHub statistics for all users'
        },
        {
          'name': 'update_leetcode_stats',
          'description': 'Updates LeetCode statistics for all users'
        },
        {
          'name': 'view_interview_pool',
          'description': 'View the interview pool (current signups)'
        },
        {
          'name': 'put_all_users_in_pool',
          'description': 'Puts all users in the pool with random availability'
        },
        {
          'name': 'send_notifications_for_active_interviews',
          'description': 'Send notifications for active interviews'
        },
        {
          'name': 'add_user_to_pool',
          'description': 'Add a user to the interview pool for this week'
        },
        {
           'name': 'verify_account',
           'description': 'Verify a user\'s SWECC account with their Discord'
        }
    ]

    def get(self, request):
        return Response({
            'available_commands': self.ALLOWED_COMMANDS
        })

    def post(self, request):
        command = request.data.get('command')
        args = request.data.get('args', [])
        kwargs = request.data.get('kwargs', {})

        if command is None or command == '' or command == 'help':
            return Response({
                'error': ''.join([
                    f' - {cmd["name"]}: {cmd["description"]}\n'
                    for cmd in self.ALLOWED_COMMANDS
                ])
            }, status=400)

        if not any(cmd['name'] == command for cmd in self.ALLOWED_COMMANDS):
            return Response({
                'error': f'Command {command} is not allowed'
            }, status=400)


        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            call_command(command, *args, **kwargs)
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            return Response({
                'success': True,
                'output': output,
                'error': error
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
            
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
