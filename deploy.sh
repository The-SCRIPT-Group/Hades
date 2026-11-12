#!/usr/bin/env bash

function run_cmd() {
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null deploy@$SERVER_IP "$*"
}

eval $(ssh-agent)
ssh-add - <<< $SSH_KEY
run_cmd "git -C Hades fetch origin master"
run_cmd "git -C Hades reset --hard origin/master"
run_cmd "sudo systemctl restart hades"
eval $(ssh-agent -k)
