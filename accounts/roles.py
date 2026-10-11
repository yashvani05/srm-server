ADMIN = "ADMIN"
EMPLOYEE = "EMPLOYEE"

API_PERMISSIONS = {
    "requests.read": "service_requests.read_requests",
    "requests.create": "service_requests.create_requests",
    "requests.update": "service_requests.update_requests",
    "requests.delete": "service_requests.delete_requests",
    "requests.status.update": "service_requests.update_request_status",
    "dashboard.read": "service_requests.read_dashboard",
}

ROLE_PERMISSIONS = {
    ADMIN: list(API_PERMISSIONS),
    EMPLOYEE: ["requests.read", "requests.create", "requests.update", "dashboard.read"],
}
