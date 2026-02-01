def test_health_check(client):
    """Prueba simple para ver si la API responde"""
    # Asumiendo que tienes un endpoint raíz o de health, si no, probamos uno que exista
    # Si no tienes endpoint raíz "/", prueba uno que sepas que responde, ej: login fallido
    response = client.get("/docs") # Docs siempre debería estar
    assert response.status_code == 200