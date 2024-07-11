from flask import Flask, send_from_directory
import os


def create_app():
    app = Flask(__name__)

    app.config['UPLOAD_FOLDER'] = 'app/static/'

    from .routes import register_routes
    register_routes(app)

        
    @app.route('/image/<path:filename>')
    async def serve_image(filename):
        image_folder = os.path.join(app.config['UPLOAD_FOLDER'])
        return send_from_directory(image_folder, filename)

    return app

