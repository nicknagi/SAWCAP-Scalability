#!/bin/bash

ps aux | grep bash | awk '{print $2}' | xargs kill
pkill python3
ps aux | grep bash
ps aux | grep python3
