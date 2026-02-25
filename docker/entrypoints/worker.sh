#!/bin/sh
set -eu

taskiq worker task_service.presentation.taskiq.broker:broker
