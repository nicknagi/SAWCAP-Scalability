#!/usr/bin/python3
import digitalocean
import os

token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN")
manager = digitalocean.Manager(token=token)
manager.get_all_domains()

print(f"Droplet limit: {manager.get_account().droplet_limit}")
print(f"Remaining requests for the hour: {manager.ratelimit_remaining}")