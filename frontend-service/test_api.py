from app import create_app

app = create_app()
ctx = app.app_context()
ctx.push()

with app.test_client() as client:
    response = client.get('/api/list-json')
    print('Status code:', response.status_code)
    print('Response data:', response.get_json())