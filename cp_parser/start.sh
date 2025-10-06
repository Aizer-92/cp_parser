#!/bin/bash
cd web_interface
exec gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} app:app

