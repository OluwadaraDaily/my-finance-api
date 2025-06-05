from setuptools import setup, find_packages

setup(
    name="my-finance-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "alembic",
        "python-jose",
        "passlib",
        "python-multipart",
        "pytest",
        "httpx"
    ],
    python_requires=">=3.10",
) 