def main(context):
    # Log some info to the Appwrite console
    context.log("Hello, Appwrite! The function has started.")

    # Check if the request is a GET or POST
    method = context.req.method
    
    # Get data from the request body (if provided)
    payload = context.req.body or {}

    # Logic: Return a simple greeting
    name = payload.get("name", "Guest")
    
    return context.res.json({
        "message": f"Hello {name}!",
        "method": method,
        "status": "success"
    })
