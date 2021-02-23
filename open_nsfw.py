from app import create_app

app = create_app()


if __name__ == '__main__':
    app.run(debug=False, load_dotenv=True, port=5001)
