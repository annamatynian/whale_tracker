#!/bin/bash
# PM2 Ecosystem Configuration for Whale Tracker

# This file defines how PM2 should run the whale tracker

module.exports = {
  apps: [{
    name: 'whale-tracker-scheduler',
    script: 'run_scheduler.py',
    interpreter: 'python3',
    cwd: '/home/ubuntu/whale-tracker',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    error_file: 'logs/pm2-error.log',
    out_file: 'logs/pm2-out.log',
    log_file: 'logs/pm2-combined.log',
    time: true,
    merge_logs: true
  }]
};
