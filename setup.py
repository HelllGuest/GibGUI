    from setuptools import setup, find_packages

    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

    setup(
        name="GibGUI",
        version="0.1.0",
        author="Anoop Kumar",
        author_email="helllguest@pm.me",
        description="GUI wrapper for gibMacOS",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/HelllGuest/GibGUI",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        python_requires=">=3.6",
        install_requires=["requests>=2.25.1"],
        entry_points={
            "console_scripts": [
                "gibgui=gibgui:launch",
            ],
        },
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
    )
