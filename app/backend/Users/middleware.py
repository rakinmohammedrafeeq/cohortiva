class SecurityHeadersMiddleware:
    """
    Add security headers to protect authentication flows.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add Referrer-Policy to prevent token leakage
        response['Referrer-Policy'] = 'no-referrer'
        
        # Add security headers for authentication endpoints
        if request.path.startswith('/api/users/'):
            # Prevent MIME type sniffing
            response['X-Content-Type-Options'] = 'nosniff'
            # Prevent clickjacking
            response['X-Frame-Options'] = 'DENY'
        
        return response
