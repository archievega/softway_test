#!/bin/sh
set -eu

taskiq worker task_service.presentation.taskiq.worker_broker:broker
