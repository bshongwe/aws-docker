FROM public.ecr.aws/docker/library/python:3.8

# Set environment variables
ENV LOG_FILE=/tmp/sample-app/sample-app.log
ENV PORT=8000
ENV MAX_LOG_SIZE=1048576

# Add sample application
ADD application.py /tmp/application.py

# Expose the port the app will run on
EXPOSE 8000

# Install any dependencies
# using Flask or other libraries:
RUN pip install Flask

# Run the application
ENTRYPOINT ["python", "/tmp/application.py"]
