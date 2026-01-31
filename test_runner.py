import os
import subprocess
import sys

def run_command(cmd, cwd=None):
    try:
        # Use shell=True for windows commands
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def test_examples():
    examples_dir = "examples"
    build_dir = "build"
    
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
        
    vibe_files = [f for f in os.listdir(examples_dir) if f.endswith(".vibe")]
    
    # Exclude modules that don't have main or are meant to be imported
    exclude = ["utils.vibe", "utils_vm.vibe"]
    
    results = []
    
    print(f"Testing {len(vibe_files)} VibeLang examples...\n")
    print(f"{'Example':25} | {'VM Backend':12} | {'C Backend'}")
    print("-" * 60)
    
    for vibe_file in vibe_files:
        if vibe_file in exclude:
            continue
            
        path = os.path.join(examples_dir, vibe_file)
        
        # 1. Test VM Backend
        vm_code, _, _ = run_command(f"python main.py {path}")
        vm_status = "PASS" if vm_code == 0 else "FAIL"
        
        # 2. Test C Backend
        # Generate C and EXE in the build directory
        base_name = vibe_file.replace(".vibe", "")
        c_file = os.path.join(build_dir, f"{base_name}_test.c")
        exe_file = os.path.join(build_dir, f"{base_name}_test.exe")
        
        # Remove old artifacts if they exist
        if os.path.exists(c_file): os.remove(c_file)
        if os.path.exists(exe_file): os.remove(exe_file)
        
        c_status = "FAIL (Transpile)"
        tp_code, _, _ = run_command(f"python main.py {path} --emit-c {c_file}")
        
        if tp_code == 0:
            build_code, _, _ = run_command(f"vibe_compile.bat {c_file}")
            if build_code == 0:
                run_code, _, _ = run_command(f".\\{exe_file}")
                c_status = "PASS" if run_code == 0 else "FAIL (Run)"
            else:
                c_status = "FAIL (Build)"
        
        print(f"{vibe_file:25} | {vm_status:12} | {c_status}")
        results.append((vibe_file, vm_status, c_status))

        # Cleanup artifacts
        try:
            if os.path.exists(c_file): os.remove(c_file)
            obj_file = exe_file.replace(".exe", ".obj")
            if os.path.exists(obj_file): os.remove(obj_file)
            if os.path.exists(exe_file): os.remove(exe_file)
            # Cleanup any other potential artifacts in build dir for this test
            pdb_file = exe_file.replace(".exe", ".pdb")
            if os.path.exists(pdb_file): os.remove(pdb_file)
        except:
            pass

    # Summary report
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)
    
    total = len(results)
    vm_passed = sum(1 for r in results if r[1] == "PASS")
    c_passed = sum(1 for r in results if r[2] == "PASS")
    
    for vibe_file, vm_status, c_status in results:
        indicator = "OK" if vm_status == "PASS" and c_status == "PASS" else "!!"
        print(f"{indicator} {vibe_file:23} | VM: {vm_status:8} | C: {c_status}")
        
    print("-" * 60)
    print(f"VM Backend: {vm_passed}/{total} passed")
    print(f"C Backend:  {c_passed}/{total} passed")
    
    if vm_passed == total and c_passed == total:
        print("\nALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\nSOME TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(test_examples())
