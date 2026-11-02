FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags "-s -w" -o /out/events .

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=build /out/events /events
USER nonroot:nonroot
EXPOSE 8095
HEALTHCHECK NONE
ENTRYPOINT ["/events"]
