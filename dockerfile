#__copyright__   = "Copyright 2024, VISA Lab"
#__license__     = "MIT"

ARG FUNCTION_DIR="/home/app/"
ARG RUNTIME_VERSION="3.8"
ARG DISTRO_VERSION="3.12"

FROM alpine:latest
FROM python:${RUNTIME_VERSION}-slim AS python-alpine

RUN python${RUNTIME_VERSION} -m pip install --upgrade pip

FROM python-alpine AS build-image

ARG FUNCTION_DIR
ARG RUNTIME_VERSION

RUN mkdir -p ${FUNCTION_DIR}

RUN python${RUNTIME_VERSION} -m pip install awslambdaric --target ${FUNCTION_DIR}

FROM python-alpine
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod 755 /usr/bin/aws-lambda-rie

RUN apt-get update 
RUN apt-get install -y ffmpeg

COPY requirements.txt ${FUNCTION_DIR}

COPY face_recognition_additional_files/tmp/data.pt /tmp/data.pt
COPY face_recognition_additional_files/tmp/data.pt ${FUNCTION_DIR}/tmp/data.pt

RUN python${RUNTIME_VERSION} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --target ${FUNCTION_DIR}
RUN python${RUNTIME_VERSION} -m pip install facenet_pytorch --no-deps --target ${FUNCTION_DIR}

RUN python${RUNTIME_VERSION} -m pip install -r requirements.txt --target ${FUNCTION_DIR}
COPY entry.sh /

COPY entry.sh ${FUNCTION_DIR}

COPY video-splitting.py ${FUNCTION_DIR}
COPY face-recognition.py ${FUNCTION_DIR}
RUN chmod 777 /entry.sh

ENTRYPOINT [ "/entry.sh" ]
CMD [ "video-splitting.video_splitting" ]