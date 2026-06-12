"""
Realistic sample call transcripts for CERA India IVR demo.
Mix of English, Hindi, and Gujarati — real complaint scenarios.
"""

SAMPLE_CALLS = [
    {
        "language": "english",
        "duration": 187,
        "transcript": (
            "Agent: Welcome to CERA customer care. How can I help you today? "
            "Customer: Hi, I purchased a CERA Aria wash basin about 2 months ago and it has started leaking from the base. "
            "The seal seems to have broken. I need someone to come and fix it. "
            "Agent: I understand, sir. Can you please confirm your address and the purchase date? "
            "Customer: Yes, my address is 45 Satellite Road, Ahmedabad. I purchased it on 15th November. "
            "Agent: Thank you. I have registered your complaint. A technician will visit within 48 hours. "
            "Your complaint number is CER-2025-4521. "
            "Customer: Okay thank you."
        ),
        "expected_category": "product_issue",
        "expected_sentiment": "neutral",
    },
    {
        "language": "hindi",
        "duration": 243,
        "transcript": (
            "Agent: CERA customer care mein aapka swagat hai. "
            "Customer: Haan, mujhe bahut problem ho rahi hai. Maine ek mahina pehle CERA ka bathroom fitting liya tha "
            "lekin installation ke time plumber ne galat pipe connect kar di aur ab pani leak ho raha hai. "
            "Main bahut pareshan hoon, teen din se yahi problem hai aur koi solution nahi mila. "
            "Agent: Maafi chahta hoon sir, aapko itni takleef hui. Kripya apna address batayein. "
            "Customer: Mera address hai 12 Vastrapur, Ahmedabad. "
            "Agent: Hum aaj shaam tak ek technician bhejenge. Complaint number CER-2025-4522 note karein. "
            "Customer: Theek hai lekin please jaldi bhejiye, bahut pareshani ho rahi hai."
        ),
        "expected_category": "installation",
        "expected_sentiment": "frustrated",
    },
    {
        "language": "gujarati",
        "duration": 156,
        "transcript": (
            "Agent: CERA customer care ma aapnu swagat che. Su seva karvi? "
            "Customer: Mane 20 din pehla ek shower set order karyo hato pan haju deliver nathi thayo. "
            "Online tracking ma show thay che ke out for delivery che pachi 5 din thai gaya. "
            "Su thayu che? "
            "Agent: Sir, aapno order number aapi shako? "
            "Customer: Haa, CER-ORD-78542 che. "
            "Agent: Jovi rahyo chhu... sir, aapno order warehouse ma delay thayo che. "
            "2 din ma pahonchi jashe. Maafi mangiye chiye. "
            "Customer: Theek che, pan please confirm karo."
        ),
        "expected_category": "delivery",
        "expected_sentiment": "neutral",
    },
    {
        "language": "english",
        "duration": 98,
        "transcript": (
            "Customer: I want to know the warranty on the CERA Magnum one piece toilet I bought last year. "
            "Agent: CERA Magnum comes with a 5-year warranty on the vitreous body and 1-year on fittings. "
            "Customer: Okay great, because one of the fittings has a crack. Is it covered? "
            "Agent: Yes sir, if it's within one year from purchase it is covered. "
            "I'll register a warranty claim for you. "
            "Customer: Perfect, thank you. That's really helpful."
        ),
        "expected_category": "warranty",
        "expected_sentiment": "satisfied",
    },
    {
        "language": "hindi",
        "duration": 312,
        "transcript": (
            "Customer: Mera naam Rajesh hai aur main bahut naraaz hoon. "
            "Maine 3 mahine pehle bathroom renovation karaya tha jisme CERA ke products liye the. "
            "Ek mahine baad hi ek tap leakage ho gaya. Complaint kiya tha, technician aaya, kuch kiya aur chala gaya. "
            "Ek hafte baad phir se same problem. Dobara complaint ki, koi nahi aaya. "
            "Aab teri mahina ho gaya hai, pani waste ho raha hai, biil badh raha hai. Ye bilkul acceptable nahi hai. "
            "Agent: Sir, main aapki baat samajh raha hoon. Ye bahut frustrating situation hai. "
            "Main abhi escalate karta hoon. Kal subah 10 baje senior technician aayega. "
            "Customer: Agar kal nahi aaya toh main consumer forum jaaunga. "
            "Agent: Sir, hum poori koshish karenge. Complaint CER-2025-4523 escalate ho gayi hai."
        ),
        "expected_category": "product_issue",
        "expected_sentiment": "frustrated",
    },
    {
        "language": "english",
        "duration": 67,
        "transcript": (
            "Customer: Hi, I just wanted to ask where I can find a CERA dealer near Bopal area in Ahmedabad. "
            "Agent: Sure sir, we have two dealers near Bopal — "
            "Sai Sanitaryware at Sindhu Bhavan Road and Modern Tiles near Bopal Cross Roads. "
            "Customer: Oh great, is there any ongoing offer currently? "
            "Agent: Yes, there's a 10% discount on select products till end of this month. "
            "Customer: Perfect, thank you so much! "
            "Agent: Happy to help. Have a great day!"
        ),
        "expected_category": "general_inquiry",
        "expected_sentiment": "satisfied",
    },
    {
        "language": "english",
        "duration": 201,
        "transcript": (
            "Customer: I received an invoice for my CERA order and the amount charged is different from what was quoted. "
            "I was quoted 8,500 rupees but was charged 9,200 rupees. "
            "Agent: I'm sorry for the confusion sir. Can you share your order number? "
            "Customer: It's CER-ORD-91023. "
            "Agent: Looking at your order, the difference is because GST was calculated separately. "
            "Your base price was 8,500 and GST at 18% makes it 10,030. "
            "Actually wait — I see the invoice shows 9,200. Let me check further. "
            "Customer: Please check, because I want clarity on this. "
            "Agent: You're right sir, there seems to be a discrepancy. "
            "I'm raising this to our billing team. You'll get a call back within 24 hours."
        ),
        "expected_category": "billing",
        "expected_sentiment": "neutral",
    },
    {
        "language": "hindi",
        "duration": 175,
        "transcript": (
            "Customer: Namaste, maine CERA Elegance series ka geyser 6 mahine pehle liya tha. "
            "Abhi kuch dino se wo theek se garam nahi kar raha. Temperature low rehta hai. "
            "Agent: Aapne installation kab karaya tha? "
            "Customer: Installation delivery ke ek din baad hua tha. "
            "Agent: Sir, yeh 6 months ke andar aa raha hai toh warranty mein cover hoga. "
            "Main ek service request dalta hoon. Ek technician 2 din mein aayega. "
            "Customer: Theek hai. Koi extra charge toh nahi hoga? "
            "Agent: Nahi sir, warranty period mein koi charge nahi. "
            "Customer: Bahut bahut shukriya."
        ),
        "expected_category": "warranty",
        "expected_sentiment": "satisfied",
    },
    {
        "language": "english",
        "duration": 89,
        "transcript": (
            "Customer: I'm calling because I ordered a CERA floor mounted EWC online three weeks ago. "
            "I got a confirmation email but no delivery yet. The website says delivered but I never received it. "
            "Agent: That's strange sir. Let me check your order CER-ORD-88741. "
            "Our records show delivery was attempted on 5th January but nobody was home. "
            "A reattempt is scheduled. "
            "Customer: Nobody informed me of any attempted delivery. Can you reschedule for Saturday? "
            "Agent: Yes sir, I'll schedule it for this Saturday morning between 10 and 12. "
            "Customer: Thank you."
        ),
        "expected_category": "delivery",
        "expected_sentiment": "neutral",
    },
    {
        "language": "gujarati",
        "duration": 134,
        "transcript": (
            "Customer: Mara bathroom ma jo CERA no tap lagyelo che, teno handle todai gayo che. "
            "Hu ek mahino j use karyo chhu. Aa quality su che? "
            "Agent: Sir, aa sambhali ne dukh thayun. Kaya model nu tap che? "
            "Customer: Mane nathi khabar exact model, pan silver color no wall mounted che. "
            "Agent: Koi vata nahi. Aap invoice number aapi shako? "
            "Customer: Haa, CER-INV-2024-7823 che. "
            "Agent: Dekhyu sir, ek mahina j thayo che toh free replacement lashe. "
            "3 din ma navo tap moklashu. "
            "Customer: Theek che, thanks."
        ),
        "expected_category": "product_issue",
        "expected_sentiment": "neutral",
    },
]
