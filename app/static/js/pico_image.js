//Default "DIY Brew"
var recipe_img = '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffe000ffc01ffffc0000000000000003fff0003f601ff7ff0000000000000000fe7c00dff003de7f8000800030000000ff3e000ff801ff7f80078001fe000000dfbe000ff801feff80070001fe0000009c37000de000dffc0007803ffe0000021c070001c000cbf80007803ffe000000dcbf800dc0002ff0000780ffff000000fc9f800fc0003fe00007a3ffff800003fc1f800fc0000dc00007ffffff000003fc3f801dc0000fc00007f1f8bf000002bcb7800dc0000dc00007f0f9fffc00003c278001c00021c00007f079ff0600023c0f8021c00021c00007fe10fe0200003c1f8001c00021c00007e000ff00000c1c3f00c1c000c1c00007e080ff00000000fe0080600000600007e010ff00000ffffc00fff000fff00007e001ff00000ffff800fff800fff80007e001ff000007ffe0007ff8003ff80007f000fe00000000000000000000000007f001fe00fffe03fff003fffcfffbff87f001fe001fffc0ffff03fffcffffffc7e0007e00cfff633c3f807e3e1cfdede7e0017e006fffb13f9fc03f9f3dfdefe7e0017e000ffff8bfefc03fdf3cffe7e7e0017e0007eef8b7ffe037df1cfdf787f0017e0001e6bc87a7e0073f18f8ff07f0017e0005cc3c841bf02fbf1aefff07f8dffe02070d7c3c3ff030df1e4ece07fdffff8c24067c303fe0ffe00e0e4e07fdffff003df778f79bc0ffe00f1f0e07fddffe010dff30bfcdf0afec0f1f0e07fc08ff7015fd38afedb82fce0f1e1e07fffffe0001e4388f21bc8f0f061e1c07fffffc0001e03c8f203c0f4f061e1c07e0017c0061f07f07003d078f063e1c07c0003e000000fe01987c000f033f1c03e0007c00ffffffffcfffffff03fff800ff9ff000fffffbffeffbffff03fbf800000000007fffe1ffe3f1ffff00f9f800000000001fff00ffc0c0fffe007070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000';

var recipe_images = {
  "": recipe_img // hardcoded for default recipe created from new_pico_recipe.html
}

//Load Default image
function load_image(recipe_id, recipe_image){
    var canvas = document.getElementById(recipe_id);
    var ctx = canvas.getContext('2d');
    var img = ctx.createImageData(canvas.width, canvas.height);
    var bytes = hexToBytes(recipe_image);
    var byte_cnt = 0;
    bytes.forEach( function(byte) {
      for (var i = 7; i >= 0; i--) {
        var val = ((byte >> i) & 1) ? 1 : 0;
        img.data[byte_cnt++] = val * 255; //R
        img.data[byte_cnt++] = val * 255; //G
        img.data[byte_cnt++] = val * 255; //B
        img.data[byte_cnt++] = 255;       //A
      }
    });
    ctx.putImageData(img, 0, 0);
}

// Load New Image - required contract with html recipe_image_*(_<recipe_id>)? elements to exist
function load_new_image(e){
    var recipe_id = e.target.id == "recipe_image_loader" ? "" : e.target.id.replace("recipe_image_loader_", "");
    var element_suffix = recipe_id == "" ? "" : "_" + recipe_id
    var reader = new FileReader();
    reader.onload = function(event) {
      var img = new Image();
      img.onload = function() {
          var canvas = document.getElementById('recipe_image' + element_suffix);
          var ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height); // Resize image to 128x64
          var img_bw = ctx.getImageData(0, 0, canvas.width, canvas.height);
          var invert = (document.getElementById('recipe_image_invert' + element_suffix).checked == true);
          var threshold = parseFloat(document.getElementById('recipe_image_threshold' + element_suffix).value);
          var byte = 0;
          var byte_cnt = 0;
          recipe_images[recipe_id] = '';
          for (var i = 0; i < img_bw.data.length; i += 4) {
            var avg = (img_bw.data[i+0] + img_bw.data[i+1] + img_bw.data[i+2])/3;
            var val = (avg > threshold) ? (invert ? 0 : 1) : (invert ? 1 : 0);
            img_bw.data[i+0] = val * 255; //R
            img_bw.data[i+1] = val * 255; //G
            img_bw.data[i+2] = val * 255; //B
            img_bw.data[i+3] = 255;       //A
            byte |= val << (7 - byte_cnt++);
            if (byte_cnt == 8) {
              var tmp = byte.toString(16);
              recipe_images[recipe_id] += ((tmp.length == 1) ? ('0' + tmp) : tmp); // %02x
              byte = 0;
              byte_cnt = 0;
            }
          }
          ctx.putImageData(img_bw, 0, 0);
      }
      img.src = event.target.result;
    }
    reader.readAsDataURL(e.target.files[0]);
    e.target.value = ''; // Reset image to reload same file
}

function hexToBytes(hex){
    for (var bytes = [], i = 0; i < hex.length; i += 2)
      bytes.push(parseInt(hex.substr(i, 2), 16));
    return bytes;
}
