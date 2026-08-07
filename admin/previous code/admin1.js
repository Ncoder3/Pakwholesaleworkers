function viewProduct(button){

document.getElementById("productModal").style.display="block";

document.getElementById("modalImage").src="/images/"+button.dataset.image;

document.getElementById("modalName").innerText=button.dataset.name;

document.getElementById("modalCode").innerText=button.dataset.code;

document.getElementById("modalCategory").innerText=button.dataset.category;

document.getElementById("modalPack").innerText=button.dataset.pack;

document.getElementById("modalPieces").innerText=button.dataset.pieces;

document.getElementById("modalWholesale").innerText=button.dataset.wholesale;

document.getElementById("modalRetail").innerText=button.dataset.retail;

document.getElementById("modalStock").innerText=button.dataset.stock;

document.getElementById("modalNotes").innerText=button.dataset.notes;

}

function closeModal(){

document.getElementById("productModal").style.display="none";

}

window.onclick=function(event){

const modal=document.getElementById("productModal");

if(event.target===modal){

modal.style.display="none";

}

}

function editProduct(button){

    document.getElementById("editModal").style.display = "block";

    document.getElementById("editCode").value = button.dataset.code;

    document.getElementById("editName").value = button.dataset.name;

    document.getElementById("editCategory").value = button.dataset.category;

    document.getElementById("editPack").value = button.dataset.pack;

    document.getElementById("editPieces").value = button.dataset.pieces;

    document.getElementById("editWholesale").value = button.dataset.wholesale;

    document.getElementById("editRetail").value = button.dataset.retail;

    document.getElementById("editStock").value = button.dataset.stock;

    document.getElementById("editNotes").value = button.dataset.notes;

}


function closeEditModal(){

    document.getElementById("editModal").style.display = "none";

}

document
.getElementById("editForm")
.addEventListener("submit", function(e){

    e.preventDefault();

    const product = {

        "Product Code":
            document.getElementById("editCode").value,

        "Product Name":
            document.getElementById("editName").value,

        "Category":
            document.getElementById("editCategory").value,

        "Pack / Unit Type":
            document.getElementById("editPack").value,

        "Pieces per Pack":
            document.getElementById("editPieces").value,

        "Wholesale Price per Pack (Rs)":
            document.getElementById("editWholesale").value,

        "Suggested Retail Price per Piece (Rs)":
            document.getElementById("editRetail").value,

        "Stock Available (Packs)":
            document.getElementById("editStock").value,

        "Notes":
            document.getElementById("editNotes").value

    };

    fetch("/update_product",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify(product)

    })

    .then(response=>response.json())

    .then(result=>{

        if(result.success){

            showToast(

                "Product Updated",

                "Changes have been saved successfully."

            );

            closeEditModal();

            setTimeout(()=>{

                location.reload();

            },800);

        }

        else{

            alert("Update failed.");

        }

    });

});

function showToast(title,message){

    const toast=document.getElementById("toast");

    document.getElementById("toastTitle").innerHTML=title;

    document.getElementById("toastMessage").innerHTML=message;

    toast.classList.add("show");

    setTimeout(()=>{

        toast.classList.remove("show");

    },3000);

}