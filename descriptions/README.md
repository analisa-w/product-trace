## CSEE 4119 Spring 2025, Final Project
## Lyali Shaikh, Analisa Wood, Michael Portale
## lss2205, aaw2182, mvp2137
## README

Our project is a luxury product authenticator that uses a decentralized blockchain-based transaction system to assist with the registration, transfer, and verification of products. 

The way to run our code is the following. The way we have run this code is by running each node & the app in separate terminals. 
First, run the honest nodes. 
>> python3 node.py 5001
>> python3 node.py 5002
>> (Optionally) python3 node.py 5003

Then, run the malicious node. 
>> python3 modified_node.py 5009

Finally, run the actual app. 
>> python3 app.py 

The app uses Flask, and allows you to open the website in the following URL: http://127.0.0.1:5000
This link will automatically open on the home page. Once in the website, you can navigate to any of the following pages:
- Register a product
- Transfer a product
- Verify a product
- View blockchain 

Each of these pages are relatively self-explanatory. However, on the register page, you need to select which node you want to be making the registration request from. You can choose any of the honest nodes, or choose the one malicious node. If you choose one of the honest nodes, the registration will succeed and be added to the blockchain. If you choose the malicious node, the registration will be rejected. For the other pages, the program will default to one of the honest nodes. 

When transferring and verifying products, you will need the serial number and/or brand name of an existing product first. If you forget any of this information, you can simply open "View Blockchain" in the same tab or a new tab to find this information, then enter it on the form.  

When you are done running the program and have registered/transferred/verified/viewed as much as you want, first terminate the app process, then terminate all the node processes. The way we have been closing these programs is manually with Control^+C. 