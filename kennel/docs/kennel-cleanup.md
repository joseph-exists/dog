
stops and destroys all lxc containers



docker compose exec kennel bash -c "
  for c in \$(lxc-ls); do
    lxc-stop -n \$c -k 2>/dev/null || true
    lxc-destroy -n \$c 2>/dev/null || true
    echo \"cleaned \$c\"
  done


