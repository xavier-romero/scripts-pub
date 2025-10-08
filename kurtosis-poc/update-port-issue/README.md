# Update port issue PoC
Deploy enclave, it should run OK.
```
kurtosis run --enclave port-issue .
```

Update image from 1.28 to 1.29. It fails because the port is not available.
```
kurtosis service update --image nginx:1.29 port-issue nginx
```