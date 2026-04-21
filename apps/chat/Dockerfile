FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags "-s -w" -o /out/chat .

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=build /out/chat /chat
USER nonroot:nonroot
EXPOSE 8080
HEALTHCHECK NONE
ENTRYPOINT ["/chat"]
