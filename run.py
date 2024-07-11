from app import create_app
from app.routes import qr_reader
import threading

app = create_app()

if __name__ == '__main__':
    qr_thread = threading.Thread(target=qr_reader)
    qr_thread.start()
    # vf_thread = threading.Thread(target=gen)
    # vf_thread.start()
    app.run(debug=True, port=5006)
