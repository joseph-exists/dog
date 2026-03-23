# 1. Confirm /dev/dxg is visible inside kennel
docker compose exec kennel ls -la /dev/dxg

# 2. Confirm WSL libs are mounted and libcuda is present
docker compose exec kennel ls -la /usr/lib/wsl/lib/libcuda*

# 3. Spawn a GPU env
curl -X POST http://localhost:8090/envs \
  -H "Content-Type: application/json" \
  -H "x-kennel-secret: woohoo" \
  -d '{"flavour": "cuda", "kind": "persistent", "gpu": true}'

# 4. Check /dev/dxg is visible inside the LXC container
docker compose exec kennel \
  lxc-attach -n env-abc123 -- ls -la /dev/dxg

# 5. Check the WSL lib mount landed
docker compose exec kennel \
  lxc-attach -n env-abc123 -- ls -la /usr/lib/wsl/lib/

# 6. PyTorch GPU check
docker compose exec kennel \
  lxc-attach -n env-abc123 -- \
  su - dev -c "source /home/dev/.venvs/torch/bin/activate && python -c '
import torch
print(f\"torch:          {torch.__version__}\")
print(f\"cuda available: {torch.cuda.is_available()}\")
if torch.cuda.is_available():
    print(f\"device:         {torch.cuda.get_device_name(0)}\")
    t = torch.rand(1000, 1000).cuda()
    print(f\"tensor device:  {t.device}\")
'"

# 7. Matmul benchmark vs baseline
docker compose exec kennel \
  lxc-attach -n env-abc123 -- \
  su - dev -c "source /home/dev/.venvs/torch/bin/activate && python -c '
import torch, time
a = torch.rand(8192, 8192).cuda()
b = torch.rand(8192, 8192).cuda()
torch.cuda.synchronize()
t = time.perf_counter()
for _ in range(10):
    c = a @ b
torch.cuda.synchronize()
ms = (time.perf_counter() - t) * 100  # avg ms per iter
print(f\"matmul 8192x8192 avg: {ms:.1f}ms\")
'"

# Build in order — each layer depends on the previous
curl -X POST "http://localhost:8090/flavours/base/rebuild" -H "x-kennel-secret: your-secret"

# Wait for done, then:
curl -X POST "http://localhost:8090/flavours/dev/rebuild"  -H "x-kennel-secret: your-secret"

# Wait for done, then:
curl -X POST "http://localhost:8090/flavours/cuda/rebuild" -H "x-kennel-secret: your-secret"