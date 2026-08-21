# WebMCP local setup checklist (beta)

1. **Chrome flag**  
   - Open `chrome://flags/#enable-webmcp-testing`  
   - Set **Enabled**  
   - Relaunch Chrome  

2. **Inspector extension**  
   - Install [Model Context Tool Inspector](https://chromewebstore.google.com/detail/model-context-tool-inspec/gbpdfapgefenggkahomfgkhfehlcenpd)  
   - Extension id: `gbpdfapgefenggkahomfgkhfehlcenpd`  

3. **Demo page**  
   - Public: https://webmcp-demo-sdras.netlify.app/  
   - Or local: `~/projects/webmcp-demo` → `python3 -m http.server 8000`  

4. **Verify**  
   - Page status or inspector shows registered tools  
   - Natural-language prompt in inspector invokes a tool (not only DOM clicks)  

5. **Production origin (optional)**  
   - Register [origin trial](https://developer.chrome.com/origintrials/#/register_trial/4163014905550602241) for your origin  
   - Do **not** commit OT tokens to public template defaults  

Chrome overview: https://developer.chrome.com/docs/ai/webmcp  
