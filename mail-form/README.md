You can connect **Microsoft Forms** with **Microsoft Power Automate** to automatically send an email when someone submits a form.

Below is the **simple step-by-step flow**.

---

## 1. Create the Form

1. Go to **Microsoft Forms**
2. Create a **New Form**
3. Add questions (Name, Email, Message, etc.)
4. Copy the **Form ID** from the URL.

Example form fields:

* Name
* Email
* Request Details

---

## 2. Create Power Automate Flow

1. Open **Microsoft Power Automate**
2. Click **Create**
3. Select **Automated Cloud Flow**

Choose trigger:

**Trigger**

```
When a new response is submitted
```

Select your **Form ID**

---

## 3. Get Form Response Details

Add a new step:

Action:

```
Get response details
```

Configuration:

* **Form ID** → Select your form
* **Response ID** → Dynamic value from trigger

This step retrieves all form answers.

---

## 4. Send Email

Add another step:

Action:

```
Send an email (V2)
```

Using **Microsoft Outlook** or **Microsoft 365 Outlook**

Example configuration:

**To**

```
admin@company.com
```

**Subject**

```
New Form Submission
```

**Body**

```
Name: Name (dynamic value)

Email: Email (dynamic value)

Message:
Request Details (dynamic value)
```

Dynamic values come from **Get response details** step.

---

## 5. Save and Test

1. Click **Save**
2. Submit the form
3. Email will be sent automatically.

---

## Example Flow Structure

```
Microsoft Forms Trigger
   ↓
Get Response Details
   ↓
Send Email (Outlook)
```

---

💡 **Common improvement**
You can also:

* Send email **to the person who submitted the form**
* Store responses in **Microsoft Excel** or **Microsoft SharePoint**
* Create **approval workflows**

---

If you want, I can also show:

* **Advanced Power Automate flow (HTML formatted email)**
* **Send email to form submitter automatically**
* **Save form data to Excel + send email** (most common setup).
