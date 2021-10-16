# coding=utf-8
import logging

from requests import HTTPError

from .rest_client import AtlassianRestAPI

log = logging.getLogger(__name__)


class ServiceDesk(AtlassianRestAPI):
    """
    JIRA ServiceDesk API object
    """

    def __init__(self, *args, insightworkspaceversion=1, **kwargs):
        super(ServiceDesk, self).__init__(*args, **kwargs)
        # Initialize insight API endpoint
        self.insightworkspaceversion = insightworkspaceversion
        self.insight_workspace_id = self._get_insight_workspace_id()
        self.insight_api_endpoint = "gateway/api/jsm/insight/workspace/{0}/v{1}/".format(
            self.insight_workspace_id, self.insightworkspaceversion
        )

    # Information actions
    def get_info(self):
        """Get info about Service Desk app"""

        return self.get("rest/servicedeskapi/info", headers=self.experimental_headers)

    def get_service_desks(self):
        """
        Returns all service desks in the Jira Service Desk application
        with the option to include archived service desks

        :return: Service Desks
        """
        service_desks_list = self.get("rest/servicedeskapi/servicedesk", headers=self.experimental_headers)
        if self.advanced_mode:
            return service_desks_list
        else:
            return (service_desks_list or {}).get("values")

    def get_service_desk_by_id(self, service_desk_id):
        """
        Returns the service desk for a given service desk ID

        :param service_desk_id: str
        :return: Service Desk
        """

        return self.get(
            "rest/servicedeskapi/servicedesk/{}".format(service_desk_id),
            headers=self.experimental_headers,
        )

    # Customers actions
    def create_customer(self, full_name, email):
        """
        Creating customer user

        :param full_name: str
        :param email: str
        :return: New customer
        """
        log.warning("Creating customer...")
        data = {"fullName": full_name, "email": email}

        return self.post("rest/servicedeskapi/customer", headers=self.experimental_headers, data=data)

    def get_customer_request(self, issue_id_or_key):
        """
        Get single request

        :param issue_id_or_key: str
        :return: Customer request
        """

        return self.get(
            "rest/servicedeskapi/request/{}".format(issue_id_or_key),
            headers=self.experimental_headers,
        )

    def get_my_customer_requests(self):
        """Returning requests where you are the assignee"""
        response = self.get("rest/servicedeskapi/request", headers=self.experimental_headers)
        if self.advanced_mode:
            return response
        return (response or {}).get("values")

    def create_customer_request(
        self,
        service_desk_id,
        request_type_id,
        values_dict,
        raise_on_behalf_of=None,
        request_participants=None,
    ):
        """
        Creating customer request

        :param service_desk_id: str
        :param request_type_id: str
        :param values_dict: str/dict
        :param raise_on_behalf_of: str
        :param request_participants: list
        :return: New request
        """
        log.warning("Creating request...")
        data = {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": values_dict,
        }

        if raise_on_behalf_of:
            data["raiseOnBehalfOf"] = raise_on_behalf_of

        if request_participants:
            data["requestParticipants"] = request_participants

        param_map = {"headers": self.experimental_headers}

        if isinstance(values_dict, dict):
            param_map["json"] = data
        elif isinstance(values_dict, str):
            param_map["data"] = data

        return self.post("rest/servicedeskapi/request", **param_map)

    def get_customer_request_status(self, issue_id_or_key):
        """
        Get customer request status name

        :param issue_id_or_key: str
        :return: Status name
        """
        request = self.get(
            "rest/servicedeskapi/request/{}/status".format(issue_id_or_key),
            headers=self.experimental_headers,
        )
        if self.advanced_mode:
            return request
        if request:
            if request.get("values", []):
                return request.get("values", [])[0].get("status", {})
        return {}

    def get_customer_transitions(self, issue_id_or_key):
        """
        Returns a list of transitions that customers can perform on the request

        :param issue_id_or_key: str
        :return:
        """
        url = "rest/servicedeskapi/request/{}/transition".format(issue_id_or_key)

        return self.get(url, headers=self.experimental_headers)

    def get_request_types(self, service_desk_id):
        """
        Gets request types

        :param service_desk_id: str
        :return: all service desk request types
        """

        return self.get(
            "rest/servicedeskapi/servicedesk/{}/requesttype".format(service_desk_id),
            headers=self.experimental_headers,
        )

    # Participants actions
    def get_request_participants(self, issue_id_or_key, start=0, limit=50):
        """
        Get request participants

        :param issue_id_or_key: str
        :param start: OPTIONAL: int
        :param limit: OPTIONAL: int
        :return: Request participants
        """
        url = "rest/servicedeskapi/request/{}/participant".format(issue_id_or_key)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        response = self.get(url, params=params, headers=self.experimental_headers)
        if self.advanced_mode:
            return response
        return (response or {}).get("values")

    def add_request_participants(self, issue_id_or_key, users_list):
        """
        Add users as participants to an existing customer request
        The calling user must have permission to manage participants for this customer request

        :param issue_id_or_key: str
        :param users_list: list
        :return:
        """
        url = "rest/servicedeskapi/request/{}/participant".format(issue_id_or_key)
        data = {"usernames": users_list}

        return self.post(url, data=data, headers=self.experimental_headers)

    def remove_request_participants(self, issue_id_or_key, users_list):
        """
        Remove participants from an existing customer request
        The calling user must have permission to manage participants for this customer request

        :param issue_id_or_key: str
        :param users_list: list
        :return:
        """
        url = "rest/servicedeskapi/request/{}/participant".format(issue_id_or_key)
        data = {"usernames": users_list}

        return self.delete(url, data=data, headers=self.experimental_headers)

    # Transitions actions
    def perform_transition(self, issue_id_or_key, transition_id, comment=None):
        """
        Perform a customer transition for a given request and transition ID.
        An optional comment can be included to provide a reason for the transition.

        :param issue_id_or_key: str
        :param transition_id: str
        :param comment: OPTIONAL: str
        :return: None
        """
        log.warning("Performing transition...")
        data = {"id": transition_id, "additionalComment": {"body": comment}}
        url = "rest/servicedeskapi/request/{}/transition".format(issue_id_or_key)

        return self.post(url, headers=self.experimental_headers, data=data)

    # Comments actions
    def create_request_comment(self, issue_id_or_key, body, public=True):
        """
        Creating request comment

        :param issue_id_or_key: str
        :param body: str
        :param public: OPTIONAL: bool (default is True)
        :return: New comment
        """
        log.warning("Creating comment...")
        data = {"body": body, "public": public}
        url = "rest/servicedeskapi/request/{}/comment".format(issue_id_or_key)

        return self.post(path=url, data=data, headers=self.experimental_headers)

    def get_request_comments(self, issue_id_or_key):
        """
        Get all comments in issue

        :param issue_id_or_key: str
        :return: Issue comments
        """

        return self.get(
            "rest/servicedeskapi/request/{}/comment".format(issue_id_or_key),
            headers=self.experimental_headers,
        )

    def get_request_comment_by_id(self, issue_id_or_key, comment_id):
        """
        Get single comment by ID

        :param issue_id_or_key: str
        :param comment_id: str
        :return: Single comment
        """

        return self.get(
            "rest/servicedeskapi/request/{}/comment/{}".format(issue_id_or_key, comment_id),
            headers=self.experimental_headers,
        )

    # Organizations actions
    def get_organisations(self, service_desk_id=None, start=0, limit=50):
        """
        Returns a list of organizations in the Jira instance. If the user is not an agent,
        the resource returns a list of organizations the user is a member of.

        :param service_desk_id: OPTIONAL: str Get organizations from single Service Desk
        :param start: OPTIONAL: int The starting index of the returned objects.
                     Base index: 0. See the Pagination section for more details.
        :param limit: OPTIONAL: int The maximum number of users to return per page.
                     Default: 50. See the Pagination section for more details.
        :return:
        """
        url_without_sd_id = "rest/servicedeskapi/organization"
        url_with_sd_id = "rest/servicedeskapi/servicedesk/{}/organization".format(service_desk_id)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        if service_desk_id is None:
            return self.get(url_without_sd_id, headers=self.experimental_headers, params=params)
        return self.get(url_with_sd_id, headers=self.experimental_headers, params=params)

    def get_organization(self, organization_id):
        """
        Get an organization for a given organization ID

        :param organization_id: str
        :return: Organization
        """
        url = "rest/servicedeskapi/organization/{}".format(organization_id)

        return self.get(url, headers=self.experimental_headers)

    def get_users_in_organization(self, organization_id, start=0, limit=50):
        """
        Get all the users of a specified organization

        :param organization_id: str
        :param start: OPTIONAL: int
        :param limit: OPTIONAL: int
        :return: Users list in organization
        """
        url = "rest/servicedeskapi/organization/{}/user".format(organization_id)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        return self.get(url, headers=self.experimental_headers, params=params)

    def create_organization(self, name):
        """
        To create an organization Jira administrator global or agent
        permission is required depending on the settings

        :param name: str
        :return: Organization data
        """
        log.warning("Creating organization...")
        url = "rest/servicedeskapi/organization"
        data = {"name": name}

        return self.post(url, headers=self.experimental_headers, data=data)

    def add_organization(self, service_desk_id, organization_id):
        """
        Adds an organization to a servicedesk for a given servicedesk ID and organization ID

        :param service_desk_id: str
        :param organization_id: int
        :return:
        """
        log.warning("Adding organization...")
        url = "rest/servicedeskapi/servicedesk/{}/organization".format(service_desk_id)
        data = {"organizationId": organization_id}

        return self.post(url, headers=self.experimental_headers, data=data)

    def remove_organization(self, service_desk_id, organization_id):
        """
        Removes an organization from a servicedesk for a given servicedesk ID and organization ID

        :param service_desk_id: str
        :param organization_id: int
        :return:
        """
        log.warning("Removing organization...")
        url = "rest/servicedeskapi/servicedesk/{}/organization".format(service_desk_id)
        data = {"organizationId": organization_id}

        return self.delete(url, headers=self.experimental_headers, data=data)

    def delete_organization(self, organization_id):
        """
        Deletes an organization for a given organization ID

        :param organization_id:
        :return:
        """
        log.warning("Deleting organization...")
        url = "rest/servicedeskapi/organization/{}".format(organization_id)

        return self.delete(url, headers=self.experimental_headers)

    def add_users_to_organization(self, organization_id, users_list=[], account_list=[]):
        """
        Adds users to an organization
        users_list is a list of strings
        account_list is a list of accountIds

        :param account_list:
        :param organization_id: str
        :param users_list: list
        :return:
        """
        log.warning("Adding users...")
        url = "rest/servicedeskapi/organization/{}/user".format(organization_id)
        data = {"usernames": users_list, "accountIds": account_list}

        return self.post(url, headers=self.experimental_headers, data=data)

    def remove_users_from_organization(self, organization_id, users_list=[], account_list=[]):
        """
        Removes users from an organization
        users_list is a list of strings
        account_list is a list of accountIds

        :param organization_id: str
        :param users_list: list
        :param account_list: list
        :return:
        """
        log.warning("Removing users...")
        url = "rest/servicedeskapi/organization/{}/user".format(organization_id)
        data = {"usernames": users_list, "accountIds": account_list}

        return self.delete(url, headers=self.experimental_headers, data=data)

    # Attachments actions
    def create_attachments(self, service_desk_id, issue_id_or_key, filenames, public=True, comment=None):
        """
        Add attachment as a comment.
        Setting attachment visibility is dependent on the user's permission. For example,
        Agents can create either public or internal attachments,
        while Unlicensed users can only create internal attachments,
        and Customers can only create public attachments.
        An additional comment may be provided which will be prepended to the attachments.
        :param service_desk_id: str
        :param issue_id_or_key: str
        :param filenames: Union(List[str], str), name, if file in current directory or full path to file
        :param public: OPTIONAL: bool (default is True)
        :param comment: OPTIONAL: str (default is None)
        :return: Request info
        """
        # Create temporary attachment
        temp_attachment_ids = []
        if not isinstance(filenames, list):
            filenames = [filenames]

        for filename in filenames:
            temp_attachment_id = self.attach_temporary_file(service_desk_id, filename)
            temp_attachment_ids.append(temp_attachment_id)

        # Add attachments
        return self.add_attachments(issue_id_or_key, temp_attachment_ids, public, comment)

    def create_attachment(self, service_desk_id, issue_id_or_key, filename, public=True, comment=None):
        """
        Add attachment as a comment.
        Setting attachment visibility is dependent on the user's permission. For example,
        Agents can create either public or internal attachments,
        while Unlicensed users can only create internal attachments,
        and Customers can only create public attachments.
        An additional comment may be provided which will be prepended to the attachments.
        :param service_desk_id: str
        :param issue_id_or_key: str
        :param filename: str, name, if file in current directory or full path to file
        :param public: OPTIONAL: bool (default is True)
        :param comment: OPTIONAL: str (default is None)
        :return: Request info
        """
        log.info("Creating attachment...")
        return self.create_attachments(service_desk_id, issue_id_or_key, filename, public=public, comment=comment)

    def attach_temporary_file(self, service_desk_id, filename):
        """
        Create temporary attachment, which can later be converted into permanent attachment
        :param service_desk_id: str
        :param filename: str
        :return: Temporary Attachment ID
        """
        url = "rest/servicedeskapi/servicedesk/{}/attachTemporaryFile".format(service_desk_id)

        # no application/json content type and an additional X-Atlassian-Token header
        # https://docs.atlassian.com/jira-servicedesk/REST/4.14.1/#servicedeskapi/servicedesk/{serviceDeskId}/attachTemporaryFile-attachTemporaryFile
        experimental_headers = self.experimental_headers.copy()
        del experimental_headers["Content-Type"]
        experimental_headers["X-Atlassian-Token"] = "no-check"

        with open(filename, "rb") as file:
            result = self.post(path=url, headers=experimental_headers, files={"file": file}).get("temporaryAttachments")
            temp_attachment_id = result[0].get("temporaryAttachmentId")

            return temp_attachment_id

    def add_attachments(self, issue_id_or_key, temp_attachment_ids, public=True, comment=None):
        """
        Adds temporary attachment to customer request using attach_temporary_file function
        :param issue_id_or_key: str
        :param temp_attachment_ids: List[str], ID from result attach_temporary_file function
        :param public: bool (default is True)
        :param comment: str (default is None)
        :return:
        """
        data = {
            "temporaryAttachmentIds": temp_attachment_ids,
            "public": public,
            "additionalComment": {"body": comment},
        }
        url = "rest/servicedeskapi/request/{}/attachment".format(issue_id_or_key)

        return self.post(url, headers=self.experimental_headers, data=data)

    def add_attachment(self, issue_id_or_key, temp_attachment_id, public=True, comment=None):
        """
        Adds temporary attachment to customer request using attach_temporary_file function
        :param issue_id_or_key: str
        :param temp_attachment_id: str, ID from result attach_temporary_file function
        :param public: bool (default is True)
        :param comment: str (default is None)
        :return:
        """
        log.info("Adding attachment")
        return self.add_attachments(issue_id_or_key, [temp_attachment_id], public=public, comment=comment)

    # SLA actions
    def get_sla(self, issue_id_or_key, start=0, limit=50):
        """
        Get the SLA information for a customer request for a given request ID or key
        A request can have zero or more SLA values
        IMPORTANT: The calling user must be an agent

        :param issue_id_or_key: str
        :param start: OPTIONAL: int
        :param limit: OPTIONAL: int
        :return: SLA information
        """
        url = "rest/servicedeskapi/request/{}/sla".format(issue_id_or_key)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        response = self.get(url, params=params, headers=self.experimental_headers)
        if self.advanced_mode:
            return response
        return (response or {}).get("values")

    def get_sla_by_id(self, issue_id_or_key, sla_id):
        """
        Get customer request SLA information for given request ID or key and SLA metric ID
        IMPORTANT: The calling user must be an agent

        :param issue_id_or_key: str
        :param sla_id: str
        :return: SLA information
        """
        url = "rest/servicedeskapi/request/{0}/sla/{1}".format(issue_id_or_key, sla_id)

        return self.get(url, headers=self.experimental_headers)

    # Approvals

    def get_approvals(self, issue_id_or_key, start=0, limit=50):
        """
        Get all approvals on a request, for a given request ID/Key

        :param issue_id_or_key: str
        :param start: OPTIONAL: int
        :param limit: OPTIONAL: int
        :return:
        """
        url = "rest/servicedeskapi/request/{}/approval".format(issue_id_or_key)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        response = self.get(url, headers=self.experimental_headers, params=params)
        if self.advanced_mode:
            return response
        return (response or {}).get("values")

    def get_approval_by_id(self, issue_id_or_key, approval_id):
        """
        Get an approval for a given approval ID

        :param issue_id_or_key: str
        :param approval_id: str
        :return:
        """
        url = "rest/servicedeskapi/request/{0}/approval/{1}".format(issue_id_or_key, approval_id)

        return self.get(url, headers=self.experimental_headers)

    def answer_approval(self, issue_id_or_key, approval_id, decision):
        """
        Answer a pending approval

        :param issue_id_or_key: str
        :param approval_id: str
        :param decision: str
        :return:
        """
        url = "rest/servicedeskapi/request/{0}/approval/{1}".format(issue_id_or_key, approval_id)
        data = {"decision": decision}

        return self.post(url, headers=self.experimental_headers, data=data)

    def get_queue_settings(self, project_key):
        """
        Get queue settings on project

        :param project_key: str
        :return:
        """
        url = "rest/servicedeskapi/queues/{}".format(project_key)

        return self.get(url, headers=self.experimental_headers)

    def get_customers(self, service_desk_id, query=None, start=0, limit=50):
        """
        Returns a list of the customers on a service desk.

        The returned list of customers can be filtered using the query parameter.
        The parameter is matched against customers' displayName, name, or email.
        For example, searching for "John", "Jo", "Smi", or "Smith" will match a
        user with display name "John Smith"..

        :param query:
        :param start:
        :param limit:
        :param service_desk_id: str
        :return: the customers added to the service desk
        """
        url = "rest/servicedeskapi/servicedesk/{}/customer".format(service_desk_id)
        params = {}
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)
        if query is not None:
            params["query"] = query

        return self.get(url, headers=self.experimental_headers, params=params)

    def add_customers(self, service_desk_id, list_of_usernames=[], list_of_accountids=[]):
        """
        Adds one or more existing customers to the given service desk.
        If you need to create a customer, see Create customer method.

        Administer project permission is required, or agents if public signups
        and invites are enabled for the Service Desk project.

        :param service_desk_id: str
        :param list_of_usernames: list
        :param list_of_accountids: list
        :return: the customers added to the service desk
        """
        url = "rest/servicedeskapi/servicedesk/{}/customer".format(service_desk_id)
        data = {"usernames": list_of_usernames, "accountIds": list_of_accountids}

        log.info("Adding customers...")
        return self.post(url, headers=self.experimental_headers, data=data)

    def remove_customers(self, service_desk_id, list_of_usernames=[], list_of_accountids=[]):
        """
        Removes one or more customers from a service desk. The service
        desk must have closed access. If any of the passed customers are
        not associated with the service desk, no changes will be made for
        those customers and the resource returns a 204 success code.

        :param service_desk_id: str
        :param list_of_usernames: list
        :param list_of_accountids: list
        :return: the customers added to the service desk
        """
        url = "rest/servicedeskapi/servicedesk/{}/customer".format(service_desk_id)
        data = {"usernames": list_of_usernames, "accountIds": list_of_accountids}

        log.info("Removing customers...")
        return self.delete(url, headers=self.experimental_headers, data=data)

    def get_queues(self, service_desk_id, include_count=False, start=0, limit=50):
        """
        Returns a page of queues defined inside a service desk, for a given service desk ID.
        The returned queues will include issue counts for each queue (issueCount field)
        if the query param includeCount is set to true (default=false).

        Permissions: The calling user must be an agent of the given service desk.

        :param service_desk_id: str
        :param include_count: bool
        :param start: int
        :param limit: int
        :return: a page of queues
        """
        url = "rest/servicedeskapi/servicedesk/{}/queue".format(service_desk_id)
        params = {}

        if include_count is not None:
            params["includeCount"] = bool(include_count)
        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        return self.get(url, headers=self.experimental_headers, params=params)

    def get_issues_in_queue(self, service_desk_id, queue_id, start=0, limit=50):
        """
        Returns a page of issues inside a queue for a given queue ID.
        Only fields that the queue is configured to show are returned.
        For example, if a queue is configured to show only Description and Due Date,
        then only those two fields are returned for each issue in the queue.

        Permissions: The calling user must have permission to view the requested queue,
        i.e. they must be an agent of the service desk that the queue belongs to.

        :param service_desk_id: str
        :param queue_id: str
        :param start: int
        :param limit: int
        :return: a page of issues
        """
        url = "rest/servicedeskapi/servicedesk/{0}/queue/{1}/issue".format(service_desk_id, queue_id)
        params = {}

        if start is not None:
            params["start"] = int(start)
        if limit is not None:
            params["limit"] = int(limit)

        return self.get(url, headers=self.experimental_headers, params=params)

    def upload_plugin(self, plugin_path):
        """
        Provide plugin path for upload into Jira e.g. useful for auto deploy
        :param plugin_path:
        :return:
        """
        files = {"plugin": open(plugin_path, "rb")}
        upm_token = self.request(
            method="GET",
            path="rest/plugins/1.0/",
            headers=self.no_check_headers,
            trailing=True,
        ).headers["upm-token"]
        url = "rest/plugins/1.0/?token={upm_token}".format(upm_token=upm_token)
        return self.post(url, files=files, headers=self.no_check_headers)

    def create_request_type(
        self,
        service_desk_id,
        request_type_id,
        request_name,
        request_description,
        request_help_text,
    ):
        """
        Creating a request type
        :param request_type_id:
        :param request_help_text:
        :param service_desk_id: str
        :param request_name: str
        :param request_description: str
        """
        log.warning("Creating request type...")
        data = {
            "issueTypeId": request_type_id,
            "name": request_name,
            "description": request_description,
            "helpText": request_help_text,
        }

        url = "rest/servicedeskapi/servicedesk/{}/requesttype".format(service_desk_id)

        return self.post(url, headers=self.experimental_headers, data=data)

    def raise_for_status(self, response):
        """
        Checks the response for an error status and raises an exception with the error message provided by the server
        :param response:
        :return:
        """
        if 400 <= response.status_code < 600:
            try:
                j = response.json()
                error_msg = j["errorMessage"]
            except Exception:
                response.raise_for_status()

            raise HTTPError(error_msg, response=response)

    ### Insight Objects ###
    def _get_insight_workspace_ids(self):
        """
        Returns all Insight workspace Ids.

        :return: List
        """
        result = self.get(
            "rest/servicedeskapi/insight/workspace",
            headers=self.experimental_headers,
        )
        return [i["workspaceId"] for i in result["values"]]

    def _get_insight_workspace_id(self):
        """
        Returns the first Insight workspace ID.

        :return: str
        """
        return next(iter(self._get_insight_workspace_ids()))

    ### Insight Icon API
    # TODO Get icon {id} https://developer.atlassian.com/cloud/insight/rest/api-group-icon/#api-icon-id-get
    # TODO Get icon global https://developer.atlassian.com/cloud/insight/rest/api-group-icon/#api-icon-global-get

    ### Insight Import API
    # TODO Post import start {id} https://developer.atlassian.com/cloud/insight/rest/api-group-import/#api-import-start-id-post

    ### Insight Iql API
    def get_iql_objects(
        self,
        iql,
        page=None,
        resultperpage=None,
        includeattributes=None,
        includeattributesdeep=None,
        includetypeattributes=None,
        includeextendedinfo=None,
    ):
        """
        Find objects based on Insight Query Language (IQL)
        https://developer.atlassian.com/cloud/insight/rest/api-group-iql/#api-iql-objects-get

        Args:
            iql (str): the iql query, see https://support.atlassian.com/jira-service-management-cloud/docs/use-insight-query-language-iql/
            page (int, optional): page number. Defaults to None (use API default).
            resultperpage (int, optional): Results returned per page. Defaults to None (use API default).
            includeattributes (bool, optional): Should the objects attributes be included in the response.
                If this parameter is false only the information on the object will be returned and the object attributes will not be present.
                Defaults to None (use API default).
            includeattributesdeep (int, optional): How many levels of attributes should be included. E.g. consider an object A that has a
                reference to object B that has a reference to object C. If object A is included in the response and includeAttributesDeep=1
                object A's reference to object B will be included in the attributes of object A but object B's reference to object C will
                not be included. However if the includeAttributesDeep=2 then object B's reference to object C will be included in object
                B's attributes. Defaults to None (use API default).
            includetypeattributes (bool, optional): Should the response include the object type attribute definition for each attribute
                that is returned with the objects. Defaults to None (use API default).
            includeextendedinfo (bool, optional): Include information about open Jira issues. Should each object have information if open
                tickets are connected to the object? Defaults to None (use API default).

        Returns:
            ObjectListResult
        """
        kwargs = locals().items()
        params = dict()
        params.update({k: v for k, v in kwargs if v is not None and k not in ["self"]})

        return self.get(
            "{0}iql/objects".format(self.insight_api_endpoint),
            headers=self.experimental_headers,
            params=params,
        )

    ### Insight Object API
    def get_insight_object(self, object_id):
        """
        Get one Insight object by ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-get

        Args:
            object_id (str): The object id to operate on

        Returns:
            Object: Insight object
        """

        return self.get(
            "{0}object/{1}".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
        )

    def put_insight_object(self, object_id, objecttypeid, attributes, hasAvatar=None, avatarUUID=None):
        """
        Update an existing object in Insight
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-put

        Args:
            object_id (str): The object id to operate on
            objecttypeid (str): The object type determines where the object should be stored and which attributes are available
            attributes (list): Array<ObjectAttributeIn> - dicts containing attributes.
            hasAvatar (bool, optional): Unclear from API docs. Defaults to None.
            avatarUUID (bool, optional): The UUID as retrieved by uploading an avatar. Defaults to None.

        Returns:
            Object: Insight object updated
        """

        kwargs = locals().items()
        data = dict()
        data.update({k: v for k, v in kwargs if v is not None and k not in ["self"]})

        return self.put(
            "{0}object/{1}".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
            data=data,
        )

    def update_insight_object(self, object_id, objecttypeid=None, attributes=None, hasAvatar=None, avatarUUID=None):
        """
        Convenience function for updating an existing object in Insight without having
        to specify parameters that are not going to change.

        Args:
            object_id (str): The object id to operate on
            objecttypeid (str): The object type determines where the object should be stored and which attributes are available
            attributes (list): Array<ObjectAttributeIn> - dicts containing attributes.
            hasAvatar (bool, optional): Unclear from API docs. Defaults to None.
            avatarUUID (bool, optional): The UUID as retrieved by uploading an avatar. Defaults to None.

        Returns:
            Object: Insight object updated
        """

        o = self.get_insight_object(object_id)
        args = {
            "object_id": object_id,
            "objecttypeid": objecttypeid or o["objectType"]["id"],
            "attributes": attributes or o["attributes"],
            "hasAvatar": hasAvatar or o["hasAvatar"],
            "avatarUUID": avatarUUID or o["avatar"]["mediaClientConfig"]["fileId"],
        }

        return self.put_insight_object(**args)

    def update_insight_objects_attributes_by_name_iql(self, iql, newattributes, whatif=False):
        """
        Convenience function for updating existing object(s) using iql and attribute names with new values.

        WARNING 1: While this is convenient and powerful it can also be dangerous as it will update all
        objects returned by the iql en masse so be careful how it's wielded so that many objects are not changed
        in an unintentional way, leading to having to go through the history of the objects and undo the changes.
        There's no convenience function for reverting to values in the history... yet :-)

        WARNING 2: This function currently does not complain if you've specified an attribute by name that does not
        exist, it will do nothing and not return an error or notification. Be especially aware that the field
        names are CASE SENSITIVE so that hair is not pulled out in frustration.

        Args:
            iql (str): The iql query returning the objects to be updated.
            newattributes (dict): A dictionary where the keys are the names of the attributes to be updated and the values are the values to set for those attributes.
            whatif (bool, optional): do not commit any changes, instead return a list of the objects with the `attributes` replaced with the new attributes
            to be sent to the API.

        Returns:
            list: List of Insight object(s) updated or to be updated
        """
        # Run the iql, loop through all pages as necessary and build a list of all objects
        page, lastpage = 1, 2
        iobs, otas = [], {}
        while page < lastpage:
            results = self.get_iql_objects(iql, page=page, includeattributes=1, includetypeattributes=1)
            iobs += results.get("objectEntries", [])
            # Unclear if the API would ever return different objectTypeAttributes between different pages
            # and a dict is more useful to us anyway so convert to a dict now while doing a dupe check
            for ota in results.get("objectTypeAttributes"):
                if ota["globalId"] not in otas.keys():
                    otas[ota["globalId"]] = ota
            page = results["pageNumber"]
            lastpage = results["pageSize"]

        updates = []
        for idx, iob in enumerate(iobs):
            # build a list of updated attributes for the object
            newattrs = [
                {
                    "objectTypeAttributeId": a["objectTypeAttributeId"],
                    "objectAttributeValues": [
                        {
                            "value": newattributes[
                                otas["{0}:{1}".format(a["workspaceId"], a["objectTypeAttributeId"])]["name"]
                            ]
                        }
                    ],
                }
                for a in iob["attributes"]
                if otas["{0}:{1}".format(a["workspaceId"], a["objectTypeAttributeId"])]["name"] in newattributes.keys()
            ]
            iob["attributes"] = newattrs
            iobs[idx] = iob
            if not whatif and newattrs:
                updates.append(self.put_insight_object(iob["id"], iob["objectType"]["id"], attributes=newattrs))

        if whatif:
            return iobs

        return updates

    def delete_insight_object(self, object_id):
        """
        Delete the referenced object by id
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-delete

        Args:
            object_id (str): The object id to operate on



        Returns:
            TBA: TBA
        """
        return self.delete(
            "{0}object/{1}".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
        )

    def get_insight_object_attributes(self, object_id):
        """
        Get the attributes one Insight object by ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-attributes-get

        Args:
            object_id (str): The object id to operate on

        Returns:
            list: Array<ObjectAttribute>
        """

        return self.get(
            "{0}object/{1}/attributes".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
        )

    def get_insight_object_history(self, object_id, asc=None, abbreviate=None):
        """
        Retrieve the history entries for an Insight object
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-history-get

        Args:
            object_id (str): The object id to operate on

            asc (bool, optional): Should the historiy be retrieved in ascending order. Defaults to None (Use the Jira setting for sort order)
            abbreviate (bool, optional): Should the values returned in the history entriy be abbreviated. Defaults to None.

        Returns:
            list: Array<ObjectHistory>
        """

        kwargs = locals().items()
        params = dict()
        params.update({k: v for k, v in kwargs if v is not None and k not in ["self", "object_id"]})

        return self.get(
            "{0}object/{1}/history".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
            params=params,
        )

    def get_insight_object_referenceinfo(self, object_id):
        """
        Find all references for an object
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-id-referenceinfo-get

        Args:
            object_id (str): The object id to operate on

        Returns:
            list: Array<ObjectReferenceTypeInfo>
        """

        return self.get(
            "{0}object/{1}/referenceinfo".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
        )

    def create_insight_object(self, objecttypeid, attributes, hasAvatar=None, avatarUUID=None):
        """
        Create a new object in Insight
        https://developer.atlassian.com/cloud/insight/rest/api-group-object/#api-object-create-post

        Args:
            objecttypeid (str): The object type determines where the object should be stored and which attributes are available
            attributes (list): List of object attributes (Array<ObjectAttributeIn>)
            hasAvatar (bool, optional): If the insight object has an avatar. Defaults to None.
            avatarUUID (bool, optional): The UUID of the avatar. Defaults to None.

        Returns:
            dict: the created object without attributes
        """
        kwargs = locals().items()
        data = {
            "objectTypeId": objecttypeid,
            "attributes": attributes,
        }
        data.update({k: v for k, v in kwargs if v is not None and k not in (list(data.keys()) + ["self"])})

        return self.post(
            "{0}object/create".format(self.insight_api_endpoint),
            headers=self.experimental_headers,
            data=data,
        )

    def create_insight_object_by_attribute_name(self, objecttypeid, attributes, hasAvatar=None, avatarUUID=None):
        """
        Convenience function to create an Insight object by passing the attributes as name:value instead of having to look up the
        attribute IDs first and build the required attributes.

        Args:
            objecttypeid (str): The object type determines where the object should be stored and which attributes are available
            attributes (dict): Dictionary where the key is the name of the attribute to set and the value is the value
            hasAvatar (bool, optional): If the insight object has an avatar. Defaults to None.
            avatarUUID (bool, optional): The UUID of the avatar. Defaults to None.

        Returns:
            dict: the created object without attributes
        """
        # Get the attributes associated with the object type
        otypeattrs = self.get_object_type_attributes(objecttypeid, onlyValueEditable=True)
        # Validate that all passed attributes exist for this object types
        otattrnames = [i["name"] for i in otypeattrs]
        keycheck = all(i in otattrnames for i in attributes.keys())
        if not keycheck:
            raise ValueError(
                "Invalid attributes names passed. Passed attribute names were {0} and valid "
                "attribute names are {1}".format(list(attributes.keys()), otattrnames)
            )
        attrs = [
            {
                "objectTypeAttributeId": ota["id"],
                "objectAttributeValues": [{"value": attributes[ota["name"]]}],
            }
            for ota in otypeattrs
            if ota["name"] in attributes.keys()
        ]

        # return attrs
        return self.create_insight_object(objecttypeid, attributes=attrs, hasAvatar=hasAvatar, avatarUUID=avatarUUID)

    ### Insight Objectconnectedtickets API
    def get_insight_object_connected_tickets(self, object_id):
        """
        Relation between Jira issues and Insight objects
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectconnectedtickets/#api-objectconnectedtickets-objectid-tickets-get

        Args:
            object_id (str): The id of the object to get connected tickets for

        Returns:
            list: Tickets
        """
        return self.get(
            "{0}objectconnectedtickets/{1}/tickets".format(self.insight_api_endpoint, object_id),
            headers=self.experimental_headers,
        )

    ### Insight Objectschema API
    def list_insight_object_schemas(self, asdfasdfasdf):
        """
        Returns a list of all insight object schemas.
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-list-get

        :return: ObjectSchemaList
        """
        return self.get(
            "{0}objectschema/list".format(self.insight_api_endpoint), headers=self.experimental_headers, absolute=True
        )

    def create_insight_object_schema(self, name, objectschemakey, description):
        """
        Creates a new Insight Object Schema
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-create-post

        Args:
            name (str): Name of the Insight object schema
            objectschemakey (str): The schema key
            description (str): Description of the schema

        Returns:
            ObjectSchema: New Insight Object Schema
        """
        data = {
            "name": name,
            "objectSchemaKey": objectschemakey,
            "description": description,
        }
        return self.post(
            "{0}objectschema/create".format(self.insight_api_endpoint),
            headers=self.experimental_headers,
            data=data,
        )

    def get_insight_object_schema(self, schema_id):
        """
        Get an Insight Object Schema by ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-id-get

        Args:
            schema_id (str): id of the schema to get

        Returns:
            ObjectSchema: Insight Object Schema
        """
        return self.get(
            "{0}objectschema/{1}".format(self.insight_api_endpoint, schema_id),
            headers=self.experimental_headers,
        )

    # TODO: Put objectschema {id} https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-id-put
    # TODO: Delete objectschema {id} https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-id-delete

    def get_insight_object_schema_attributes(self, schema_id):
        """
        Get Insight Object Schema Attributes by Schema ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-id-attributes-get

        Args:
            schema_id (str): id of the schema attributes to get

        Returns:
            Array<ObjectTypeAttribute>: Array of attributes
        """
        return self.get(
            "{0}objectschema/{1}/attributes".format(self.insight_api_endpoint, schema_id),
            headers=self.experimental_headers,
        )

    def get_insight_object_schema_objecttypes_flat(self, schema_id):
        """
        Get Insight Object Schema object types by schema ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-objectschema/#api-objectschema-id-objecttypes-flat-get

        Args:
            schema_id (str): id of the schema object types to get

        Returns:
            Array<ObjectType>: Array of objects
        """
        return self.get(
            "{0}objectschema/{1}/objecttypes/flat".format(self.insight_api_endpoint, schema_id),
            headers=self.experimental_headers,
        )

    ### Insight Objecttype API
    def get_insight_object_type(self, type_id):
        """
        Get Insight Object object ID
        https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-id-get

        Args:
            type_id (str): id of the object type to get

        Returns:
            ObjectType: Insight Object Type
        """
        return self.get(
            "{0}objecttype/{1}".format(self.insight_api_endpoint, type_id),
            headers=self.experimental_headers,
        )

    def _put_insight_object_type(
        self,
        type_id,
        name,
        iconid,
        objectschemaid,
        description=None,
        parentobjecttypeid=None,
        inherited=None,
        abstractobjecttype=None,
    ):
        """
        Put an Insight object type
        https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-id-put

        Args:
            type_id (str): the ID of the type to update
            name (str): The new name
            iconid (str): The id of the icon to use
            objectSchemaId (str): The object schema ID
            description (str, optional): The updated description. Defaults to None.
            parentobjecttypeid (str, optional): The new parent object type id. Defaults to None.
            inherited (bool, optional): The new inherited value. Defaults to None.
            abstractobjecttype (bool, optional): The new abstractobjecttype value. Defaults to None.

        Returns:
            ObjectType: The updated object type
        """
        data = {
            "id": type_id,
            "name": name,
            "iconId": iconid,
            "objectSchemaId": objectschemaid,
        }
        if description is not None:
            data["description"] = description
        if parentobjecttypeid is not None:
            data["parentObjectTypeId"] = parentobjecttypeid
        if inherited is not None:
            data["inherited"] = inherited
        if abstractobjecttype is not None:
            data["abstractObjectType"] = abstractobjecttype
        return self.put(
            "{0}objecttype/{1}".format(self.insight_api_endpoint, type_id),
            headers=self.experimental_headers,
            data=data,
        )

    def update_insight_object_type(
        self,
        type_id,
        name=None,
        iconid=None,
        objectschemaid=None,
        description=None,
        parentobjecttypeid=None,
        inherited=None,
        abstractobjecttype=None,
    ):
        """
        Update an Insight object type. This is a friendlier method than
        the official _put_insight_object_type since it does not require
        that the name, iconid, objectschemaid be provided every time even
        if they do not need to be updated.
        Instead, it will get those from the existing object type
        and use the existing values.

        Args:
            type_id (str): the ID of the type to update
            name (str, optional): The new name
            iconid (str, optional): The id of the icon to use
            objectSchemaId (str, optional): The object schema ID
            description (str, optional): The updated description. Defaults to None.
            parentobjecttypeid (str, optional): The new parent object type id. Defaults to None.
            inherited (bool, optional): The new inherited value. Defaults to None.
            abstractobjecttype (bool, optional): The new abstractobjecttype value. Defaults to None.

        Returns:
            ObjectType: The updated object type
        """

        otype = self.get_insight_object_type(type_id)
        args = {
            "type_id": type_id,
            "name": name or otype["name"],
            "iconid": iconid or otype["icon"]["id"],
            "objectschemaid": objectschemaid or otype["objectSchemaId"],
            "description": description,
            "parentobjecttypeid": parentobjecttypeid,
            "inherited": inherited,
            "abstractobjecttype": abstractobjecttype,
        }

        return self._put_insight_object_type(**args)

    # TODO: Delete objecttype {id} https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-id-delete

    def get_object_type_attributes(
        self,
        type_id,
        onlyValueEditable=None,
        orderByName=None,
        query=None,
        includeValuesExist=None,
        excludeParentAttributes=None,
        includeChildren=None,
        orderByRequired=None,
    ):
        """
        Find all attributes for this object type
        https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-id-attributes-get


        Args:
            type_id (str): id of the object type
            onlyValueEditable (bool, optional): only return editable values, defaults to None (Use API default)
            orderByName (bool, optional): values, defaults to None (Use API default)
            query (str, optional): Not documented in API, defaults to None (Use API default)
            includeValuesExist (bool, optional): Include only where values exist, defaults to None (Use API default)
            excludeParentAttributes (bool, optional): Exclude parent attributes, defaults to None (Use API default)
            includeChildren (bool, optional): include attributes from children, defaults to None (Use API default)
            orderbyrequired (bool, optional): Order by required fields, defaults to None (Use API default)
        """

        kwargs = locals().items()
        params = dict()
        params.update({k: v for k, v in kwargs if v is not None and k not in ["self", "type_id"]})

        return self.get(
            "{0}objecttype/{1}/attributes".format(self.insight_api_endpoint, type_id),
            headers=self.experimental_headers,
            params=params,
        )

    # TODO: Post objecttype {id} position https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-id-position-post
    # TODO: Post objecttype create https://developer.atlassian.com/cloud/insight/rest/api-group-objecttype/#api-objecttype-create-post

    ### Insight ObjectTypeAttribute API
    # TODO: Post objecttypeattribute {objectTypeId} https://developer.atlassian.com/cloud/insight/rest/api-group-objecttypeattribute/#api-objecttypeattribute-objecttypeid-post
    # TODO: Put objecttypeattribute {objectTypeId} {id} https://developer.atlassian.com/cloud/insight/rest/api-group-objecttypeattribute/#api-objecttypeattribute-objecttypeid-id-put
    # TODO: Delete objecttypeattribute {id} https://developer.atlassian.com/cloud/insight/rest/api-group-objecttypeattribute/#api-objecttypeattribute-id-delete

    ### Insight Progess API
    # TODO: Get progress category imports {id} https://developer.atlassian.com/cloud/insight/rest/api-group-progress/#api-progress-category-imports-id-get

    ### Insight Config API
    # TODO: Get config statustype https://developer.atlassian.com/cloud/insight/rest/api-group-config/#api-config-statustype-get
    # TODO: Post config statustype https://developer.atlassian.com/cloud/insight/rest/api-group-config/#api-config-statustype-post
    # TODO: Get config statustype {id} https://developer.atlassian.com/cloud/insight/rest/api-group-config/#api-config-statustype-id-get
    # TODO: Put config statustype {id} https://developer.atlassian.com/cloud/insight/rest/api-group-config/#api-config-statustype-id-put
    # TODO: Delete config statustype {id} https://developer.atlassian.com/cloud/insight/rest/api-group-config/#api-config-statustype-id-delete
