## CSEE 4119 Spring 2025, Final Project
## Lyali Shaikh, Analisa Wood, Michael Portale
## lss2205, aaw2182, mvp2137
## TESTING

In this testing file, we will outline all the functions of our program and how we know they work properly. We will also include some edge cases to prove they have been properly handled. For all descriptions, refer to the README and assume that the nodes and app have all been run properly. 

REGISTRATION
One type of block that our program can mine is the "register" type. This functionality registers a new product and adds it to the blockchain. To do so, the user must enter the serial number, model name, and brand name of their product. The user must also ensure that they have selected one of the honest nodes to enact this transaction, not the malicious node. 
If the user has chosen a serial number that already exists, they will be taken to a registration failed page that informs them they have selected a serial number that is already in use. 
If they have done everything correctly and chosen an honest node, they will receive a success message. This block now exists on the blockchain, reinforced both by the "View Blockchain" page which will display this new block and the "Verify" page which will verify the existence of this product. 
If they have chosen a malicious node, the registration will be rejected by the program and they will be taken to a failed registration page. This block will not be added to the chain, leaving the serial number available in case someone on an honest node has the real product, and similarly will not be reflected on the "View Blockchain" or "Verify" pages as the other nodes do not allow the malicious node to add this product to the blockchain. This demonstrates the resilience of the blockchain against tampering. 

TRANSFERRING
The other type of block that can be added to the blockchain is the "transfer" type. This functionality allows the user to transfer ownership of a product from one owner or brand to a new owner. To do so, the user must enter the serial number of the product, the name of the current owner or brand, and the name of the new owner. 
If they have entered the correct information, they will be taken to a successful transfer page and the new block will be added to the blockchain, reinforced by the "View Blockchain" page and the "Verify" page, which will include that transfer in the ownership history of the product. 
If they have entered an incorrect serial number, they will be taken to a failed transfer page and be told that the serial number they entered does not exist. This message will also appear if they try to transfer a product with a serial number that a malicious node has tried to register, because that number will never be added to the blockchain. 
This page also defaults to using an honest node, so the malicious node is never even able to attempt to transfer a product. Only honest nodes are able to access this page. 

VERIFICATION
Our program also allows users to verify the existence and ownership history of products. They must enter a serial number, and they will be taken to a verification success page that displays the current owner as well as the ownership history of the product in chronological order, including initial registration and any subsequent transfers. 
If they have entered a serial number that does not exist on the blockchain, including a serial number that a malicious node attempted to register, they will be taken to a verification failed page that tells them the serial number has not been registered. 
Similarly to transferring, this page defaults to an honest node so a malicious node is unable to access this page. Even if a malicious node were able to access this page, the verification feature does not edit or alter the blockchain, it only displays a portion of it, so it would not be able to tamper with the blockchain. 

VIEW BLOCKCHAIN
Finally, our program includes a feature that allows the user to view the entire history of the blockchain. It displays each block that has been added to the blockchain up until this point, including timestamp, block number, message type, serial number, and relevant information for each message type (model and brand name for registration, former owner and new owner for transfer). 
This page also demonstrates the blockchain's ability to handle forking. If the user opens multiple pages in separate tabs, for example two different registration pages running on two different honest nodes, then registers different products at the same time, the blockchain will be able to add both within the same chain and display it accordingly. The only way an issue would occur would be if the user utilizes the same serial number twice or makes another mistake addressed above. Similarly, the user could open multiple tabs with the same node and have the blockchain display all of the blocks added. This applies to multiple honest nodes, the same honest node, the same malicious node, or a combination of the above, and to both registration and transferring. 

NODES
During all of these processes, the nodes are in peer-to-peer communication, both sending each other messages and printing information to the terminal such as their own actions and the actions of their peers that they have received information about. If any issues above occur (such as interference from a malicious node, attempted reuse of a serial number, attempted transfer or verification of a nonexistent serial number), the honest nodes respond accordingly and print, send, and receive the appropriate messages. The malicious node behaves similarly, but with the specifications that it is behaving maliciously. 

OTHER
We also have some other files in our directory —- specifically test_forking.py & send_message.py -- that we utilized during the testing process, but are not necessary for the functionality of the program. 