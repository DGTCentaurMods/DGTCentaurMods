// ==UserScript==
// @name         DGT Centaur Mods
// @namespace    http://centaur.local/
// @version      0.1
// @description  Tampermonkey script to fetch games from Modded DGT Centaur into Lichess analysis
// @author       Ed Nekebno
// @grant        GM_xmlhttpRequest
// @resource     pgnlist http://centaur.local/getgames/1
// @match        https://lichess.org/analysis
// @icon         https://www.google.com/s2/favicons?sz=64&domain=lichess.org
// ==/UserScript==

(function() {

    // Change this to the hostname you gave your raspberry PI when setting up the SD card (add ".local" to the end)
    var boardname = 'centaur.local';
    
    function getPGNById(id) {
        var pgnurl = 'http://' + boardname + '/getpgn/' + id;
        GM_xmlhttpRequest({
            method: "GET",
            url: pgnurl,
            onload: function(response) {
                document.getElementsByClassName('pair')[1].getElementsByTagName('textarea')[0].value = response.responseText;
                document.getElementById('centaurpgnlist').style.display = 'none';
                document.getElementsByClassName('pair')[1].getElementsByTagName('button')[0].click();
            }
        });
    }
    
    function getCentaurPGNs() {
        GM_xmlhttpRequest({
            method: 'GET',
            url: 'http://' + boardname + '/getgames/1',
            onload: function(response) {
                const obj = JSON.parse(response.responseText);
                var cb = document.getElementById('selectpgn');
                cb.innerHTML = '';
                var opt = document.createElement('option');
                opt.text = '';
                opt.value = -1;
                cb.options.add(opt);
                for (var x = 0; x < Object.keys(obj).length; x++) {
                    if (obj[x].result == 'None') { obj[x].result = ''; }
                    if (obj[x].created_at == 'None') { obj[x].created_at = ''; }
                    if (obj[x].source == 'None') { obj[x].source = ''; }
                    if (obj[x].event == 'None') { obj[x].event = ''; }
                    if (obj[x].site == 'None') { obj[x].site = ''; }
                    if (obj[x].round == 'None') { obj[x].round = ''; }
                    if (obj[x].white == 'None') { obj[x].white = ''; }
                    if (obj[x].black == 'None') { obj[x].black = ''; }
                    var desc = '';
                    if (obj[x].event != '') { desc = desc + obj[x].event + ',   '; }
                    if (obj[x].site != '') { desc = desc + obj[x].site + ',   '; }
                    if (obj[x].round != '') { desc = desc + obj[x].round + ',   '; }
                    if (obj[x].white != '' || obj[x].black != '') { desc = desc + obj[x].white + ' vs. ' + obj[x].black + ',   '; }
                    if (obj[x].result != '') { desc = desc + obj[x].result + ''; }
                    opt = document.createElement('option');
                    opt.text = desc;
                    opt.value = obj[x].id;
                    cb.options.add(opt);
                }
                cb.addEventListener('change', () => {
                    if (cb.value >= 0) {
                        getPGNById(cb.value);
                    }
                });
            }
        });
    }
    
    function addListChoicesBox() {
        var lcb = document.createElement('div');
        lcb.id = 'centaurpgnlist';
        lcb.style.backgroundColor = 'white';
        lcb.style.border = '1px solid gray';
        lcb.style.padding = '10px';
        lcb.style.width = '500px';
        lcb.style.height = '60px';
        lcb.style.color = 'black';
        lcb.style.marginLeft = 'auto';
        lcb.style.marginRight = 'auto';
        lcb.style.display = 'none';
        var selectpgn = document.createElement('select');
        selectpgn.id = 'selectpgn';
        selectpgn.style.width = '480px';
        selectpgn.style.color = 'black';
        selectpgn.style.backgroundColor = 'white';
        lcb.appendChild(selectpgn);
        document.body.appendChild(lcb);
    }
    
    function addCentaurButton() {
        console.log("Adding button");
        var newbutton = document.createElement('button');
        newbutton.classList.add('button');
        newbutton.classList.add('button-thin');
        newbutton.classList.add('action');
        newbutton.classList.add('text');
        newbutton.value = 'DGT Centaur';
        newbutton.innerText = 'DGTCentaur';
        newbutton.style.right = '200px';
        var pgntext = document.getElementsByClassName('pair')[1];
        pgntext.appendChild(newbutton);
        newbutton.addEventListener("click", () => {
            document.getElementById('centaurpgnlist').style.display = '';
        });
    }
    
    function addCentaurBits() {
        addCentaurButton();
        addListChoicesBox();
        getCentaurPGNs();
    }
    
    setTimeout(addCentaurBits(), 2000);
    
    })();