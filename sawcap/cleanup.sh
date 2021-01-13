#!/bin/bash

ps aux | grep bash | awk '{print $2}' | xargs kill
ps aux | grep python3 | awk '{print $2}' | xargs kill
ps aux | grep bash
ps aux | grep python3
