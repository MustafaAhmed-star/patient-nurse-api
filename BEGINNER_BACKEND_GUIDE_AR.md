# دليل المبتدئ لمشروع Ghaith Backend API

هذا الملف مخصص للمطور المبتدئ. الهدف منه ليس فقط شرح ما الموجود في المشروع، بل شرح **لماذا** اخترنا هذا الشكل، ولماذا لم نختر بدائل أخرى في هذه المرحلة.

المشروع هو Backend API فقط لمنصة خدمات طبية منزلية اسمها **غيث / Ghaith**. الواجهة ستكون Flutter لاحقا، لذلك ركزنا هنا على API نظيف، قابل للتوسع، وسهل القراءة.

---

## 1. لماذا Django؟

استخدمنا Django لأنه مناسب جدا لبناء Backend منظم بسرعة وبطريقة آمنة.

Django يوفر أشياء مهمة جاهزة:

- نظام مستخدمين وصلاحيات.
- ORM للتعامل مع قاعدة البيانات بدون كتابة SQL في كل مكان.
- Migrations لتحديث قاعدة البيانات بطريقة منظمة.
- Django Admin لإدارة البيانات من لوحة جاهزة.
- دعم جيد للترجمة واللغات.
- مجتمع كبير ودروس كثيرة، وهذا مهم للمبتدئ.

### لماذا لم نستخدم Flask؟

Flask خفيف وممتاز، لكنه يعطيك حرية كبيرة جدا. هذه الحرية مفيدة للمحترف، لكنها قد تربك المبتدئ، لأنك ستحتاج أن تختار بنفسك:

- طريقة تنظيم الملفات.
- طريقة تسجيل المستخدمين.
- طريقة الصلاحيات.
- طريقة إدارة قاعدة البيانات.
- طريقة التوثيق.

في مشروع طبي فيه مرضى وممرضين وطلبات وصلاحيات، الأفضل للمبتدئ أن يبدأ بإطار عمل منظم مثل Django.

### لماذا لم نستخدم FastAPI؟

FastAPI ممتاز وسريع، لكنه يحتاج قرارات أكثر حول:

- بنية المشروع.
- نظام المستخدمين.
- لوحة الإدارة.
- Migrations.
- الصلاحيات.

اخترنا Django لأن المشروع يحتاج لوحة Admin جاهزة، ونظام صلاحيات، وقاعدة بيانات علائقية، وكلها نقاط Django قوي فيها جدا.

---

## 2. لماذا Django REST Framework؟

Django وحده ممتاز لتطبيقات الويب، لكن هذا المشروع API فقط. لذلك استخدمنا Django REST Framework، واختصاره DRF.

DRF يساعدنا في:

- تحويل Models إلى JSON.
- استقبال JSON من Flutter والتحقق منه.
- إنشاء ViewSets وRouters بدل كتابة كل endpoint يدويا.
- إدارة الصلاحيات.
- دعم pagination و filtering و searching.
- تنظيم serializers بطريقة واضحة.

### لماذا لم نكتب API views يدويا فقط؟

ممكن نكتب كل endpoint باستخدام Django العادي، لكن هذا سيكرر كود كثير:

- قراءة request.
- التحقق من البيانات.
- تحويل البيانات إلى JSON.
- معالجة الأخطاء.
- كتابة response موحد.

DRF يقلل التكرار ويجعل الكود أسهل في التعلم والصيانة.

---

## 3. لماذا PostgreSQL؟

استخدمنا PostgreSQL لأنه قاعدة بيانات قوية ومناسبة للتطبيقات الحقيقية.

المشروع يحتوي على:

- Users.
- Profiles.
- Orders.
- OrderItems.
- Ratings.
- Notifications.
- علاقات كثيرة بين الجداول.

PostgreSQL ممتازة في العلاقات، الفهارس، المعاملات transactions، وحماية البيانات.

### لماذا لم نعتمد على SQLite؟

SQLite ممتازة للتجربة السريعة، لكنها ليست الاختيار الأفضل لمنصة حقيقية عليها مستخدمين وطلبات. مثلا عند قبول طلب بواسطة ممرض واحد فقط، نحتاج transactions و locking أقوى. PostgreSQL أنسب لهذا.

في الاختبارات يمكن استخدام SQLite مؤقتا لتسريع التحقق المحلي، لكن الإنتاج production يجب أن يكون PostgreSQL.

---

## 4. لماذا JWT Authentication؟

الواجهة ستكون Flutter، وFlutter غالبا يتعامل مع API من خلال tokens.

JWT مناسب لأن:

- المستخدم يسجل الدخول بالإيميل والباسورد.
- السيرفر يرجع `access token` و `refresh token`.
- Flutter يرسل access token مع كل request.
- لا نحتاج sessions تقليدية مرتبطة بالمتصفح.

### ما الفرق بين access و refresh؟

- `access token`: قصير العمر، يستخدم في كل request.
- `refresh token`: أطول عمرا، يستخدم للحصول على access token جديد.

### لماذا استخدمنا blacklist في logout؟

لأن JWT بطبيعته لا يحتاج أن يبقى محفوظا في السيرفر. لكن عند logout نريد إبطال refresh token. لذلك استخدمنا Simple JWT token blacklist.

---

## 5. لماذا Custom User Model؟

في Django يوجد User جاهز يستخدم `username`. لكن متطلبات المشروع تقول إن تسجيل الدخول يكون باستخدام:

- Email.
- Password.

لذلك أنشأنا User مخصص:

```python
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(...)
```

### لماذا email unique؟

لأن نفس الإيميل لا يجب أن يسجل مرة كممرض ومرة كمريض. جعل email فريد على مستوى User كله يحل هذه المشكلة من الأساس.

### لماذا لم نعمل جدول منفصل لكل نوع مستخدم؟

كان ممكنا عمل:

- Admin table.
- Nurse table.
- Patient table.

لكن هذا سيصعب تسجيل الدخول والصلاحيات. الأفضل أن يكون هناك User واحد، ثم Profile حسب الدور:

- User + NurseProfile.
- User + PatientProfile.

هذا يجعل authentication موحدا وواضحا.

---

## 6. لماذا UUID؟

استخدمنا UUID في الجداول الأساسية حتى لا تظهر IDs متسلسلة مثل:

```text
/orders/1/
/orders/2/
/orders/3/
```

الـ UUID أصعب في التخمين:

```text
/orders/5e3c9c3a-...
```

هذا مفيد في APIs التي سيتعامل معها mobile app.

### هل UUID بديل عن الصلاحيات؟

لا. UUID لا يغني أبدا عن permissions. لذلك ما زلنا نتحقق أن المريض يرى طلباته فقط، والممرض يرى الطلبات المناسبة له فقط.

---

## 7. لماذا قسمنا المشروع إلى Apps؟

بدل وضع كل شيء في app واحد، قسمنا المشروع:

```text
apps/accounts
apps/services
apps/orders
apps/notifications
```

كل app مسؤول عن مجال واضح:

- `accounts`: المستخدمين والبروفايلات وطلبات انضمام الممرضين.
- `services`: الخدمات الطبية والمناطق.
- `orders`: الطلبات والتقييمات.
- `notifications`: الإشعارات.

### لماذا هذا أفضل للمبتدئ؟

عندما تريد تعديل شيء عن الطلبات، تذهب غالبا إلى `apps/orders`. عندما تريد تعديل التسجيل، تذهب إلى `apps/accounts`. هذا يقلل التشتت.

---

## 8. لماذا استخدمنا Serializers؟

Serializer في DRF له وظيفتان مهمتان:

1. تحويل Model إلى JSON.
2. التحقق من البيانات القادمة من المستخدم.

مثلا تسجيل المريض يحتاج:

- full_name.
- phone.
- email.
- address.
- password.
- accepted_terms.

بدل التحقق من هذه الحقول داخل view بشكل عشوائي، وضعنا ذلك في `PatientRegisterSerializer`.

### لماذا لا نضع validation داخل model فقط؟

بعض التحقق مرتبط بالـ API وليس قاعدة البيانات فقط. مثلا:

- password لا يخزن كما هو.
- accepted_terms مطلوب في registration فقط.
- nurse registration يحتاج ملفات.

لذلك serializer مكان مناسب للتحقق من بيانات request.

---

## 9. لماذا استخدمنا Validators مشتركة؟

ملف:

```text
shared/validators/common.py
```

يحتوي على:

- Egyptian phone validation.
- letters-only name validation.
- strong password validation.
- upload validation.

### لماذا لم نكرر validation في كل Serializer؟

التكرار خطر. لو غيرنا صيغة رقم الهاتف في مكان ونسينا مكان آخر، سيحدث سلوك غير موحد. لذلك وضعنا validators مشتركة ونستخدمها في أكثر من مكان.

---

## 10. لماذا Service Layer؟

بعض العمليات ليست CRUD بسيط. مثال قبول طلب:

- التأكد أن الطلب ACTIVE.
- التأكد أن الممرض معتمد.
- التأكد أن الممرض ليس لديه طلب IN_PROGRESS.
- تعيين الممرض.
- تغيير status.
- إرسال notifications.

لو وضعنا كل هذا داخل view سيصبح view طويل وصعب القراءة. لذلك أنشأنا:

```text
apps/orders/services.py
```

وفيه دوال مثل:

- `create_order`
- `accept_order`
- `complete_order`
- `nurse_cancel_order`
- `admin_change_order_status`

### لماذا هذا مهم؟

لأن business rules يجب أن تكون واضحة ومركزة في مكان واحد. لو احتجنا استخدام نفس المنطق من admin أو من background job لاحقا، لن نكرر الكود.

---

## 11. لماذا استخدمنا Transactions؟

عند قبول الطلب، لا نريد أن يقبل ممرضان نفس الطلب في نفس اللحظة.

لذلك استخدمنا:

```python
@transaction.atomic
select_for_update()
```

هذا يجعل قاعدة البيانات تقفل الصف أثناء العملية، فتمنع تعارض البيانات.

### لماذا لم نكتف بفحص status فقط؟

لأن فحص status بدون transaction قد يفشل في حالة ضغط حقيقي. ممرضان قد يقرآن نفس الطلب كـ ACTIVE في نفس اللحظة، ثم كلاهما يقبله. transaction تقلل هذا الخطر.

---

## 12. لماذا هذه حالات الطلب؟

استخدمنا:

- `ACTIVE`
- `PENDING`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`

### معنى كل حالة

- `ACTIVE`: الطلب ظاهر للممرضين المعتمدين.
- `PENDING`: حالة إدارية، يستخدمها admin للمراجعة أو إعادة فتح طلب مكتمل.
- `IN_PROGRESS`: ممرض قبل الطلب ويعمل عليه.
- `COMPLETED`: الطلب انتهى.
- `CANCELLED`: الطلب ملغي.

### لماذا عند accept ننتقل إلى IN_PROGRESS؟

لأنك طلبت أن قبول الممرض يجعل الطلب قيد التنفيذ مباشرة. لذلك flow الطبيعي:

```text
ACTIVE -> IN_PROGRESS -> COMPLETED
```

وإذا الممرض ألغى:

```text
IN_PROGRESS -> ACTIVE
```

---

## 13. لماذا Snapshot للأسعار؟

عند إنشاء order، نخزن:

- اسم الخدمة وقت الطلب.
- سعر الخدمة وقت الطلب.
- اسم المنطقة وقت الطلب.
- سعر المواصلات وقت الطلب.
- final price.

### لماذا لا نحسب السعر دائما من Service و Area؟

لأن admin قد يغير السعر لاحقا. لو طلب قديم كان سعره 100، ثم الخدمة أصبحت 150، لا نريد أن يتغير الطلب القديم. الطلب يجب أن يحفظ السعر الذي وافق عليه المريض وقت الإنشاء.

هذا هو معنى price snapshot.

---

## 14. لماذا Soft Delete للخدمات والمناطق؟

لو حذفنا خدمة من قاعدة البيانات بشكل نهائي، قد تتأثر الطلبات القديمة المرتبطة بها.

لذلك استخدمنا:

- `is_active`
- `is_deleted`
- `deleted_at`

الحذف يجعل الخدمة غير ظاهرة للطلبات الجديدة، لكن الطلبات القديمة تبقى سليمة.

---

## 15. لماذا Permissions مخصصة؟

المشروع فيه أدوار مختلفة:

- Admin.
- Approved Nurse.
- Patient.

لذلك أنشأنا permissions مثل:

- `IsAdminRole`
- `IsPatientRole`
- `IsApprovedNurseRole`
- `IsAuthenticatedAndNotBlocked`

### لماذا لا نتحقق داخل كل view؟

لو كتبنا:

```python
if request.user.role != ...
```

في كل view، سنكرر الكود. permissions تجعل القاعدة واضحة وقابلة لإعادة الاستخدام.

---

## 16. لماذا Notifications منفصلة؟

الإشعارات جزء مستقل من النظام. يمكن أن تحدث بسبب:

- تسجيل ممرض.
- موافقة admin.
- إنشاء طلب.
- قبول طلب.
- إكمال طلب.
- تقييم.

لذلك أنشأنا app خاص:

```text
apps/notifications
```

### لماذا خزنا notification في قاعدة البيانات؟

حتى يستطيع المستخدم فتح التطبيق لاحقا ويرى الإشعارات القديمة أو unread count.

### لماذا email أيضا؟

لأن بعض الأحداث مهمة، مثل قبول أو رفض ممرض. لكن email في التطوير يستخدم console backend حتى لا نحتاج SMTP حقيقي أثناء التجربة.

---

## 17. لماذا Response Format موحد؟

كل response يرجع بهذا الشكل:

```json
{
  "success": true,
  "message": "Request completed successfully.",
  "data": {}
}
```

هذا يسهل على Flutter التعامل مع النتائج، لأن شكل response ثابت.

### لماذا لم نرجع JSON عادي مباشرة؟

لو كل endpoint يرجع شكل مختلف، سيصبح frontend أكثر تعقيدا. الشكل الموحد يقلل الأخطاء.

---

## 18. لماذا Pagination و Filtering و Search؟

عندما يزيد عدد الطلبات أو المستخدمين، لا يمكن إرسال كل البيانات دفعة واحدة.

Pagination تجعل API يرجع صفحة صغيرة:

```json
{
  "count": 100,
  "next": "...",
  "previous": null,
  "results": []
}
```

Filtering و Search مهمان للوحة admin:

- البحث عن مريض بالإيميل.
- فلترة الطلبات حسب status.
- ترتيب الخدمات حسب السعر.

---

## 19. لماذا استخدمنا .env؟

الإعدادات الحساسة لا يجب أن تكون داخل الكود.

أمثلة:

- SECRET_KEY.
- DATABASE_URL.
- EMAIL_HOST_PASSWORD.

لذلك وضعنا ملف:

```text
.env.example
```

هذا مثال فقط. أما `.env` الحقيقي فلا يدخل GitHub.

---

## 20. لماذا Django Admin بالإضافة إلى API؟

المشروع يحتاج Admin يدير النظام. لدينا REST APIs للـ admin، لكن Django Admin مفيد جدا في البداية لأنه:

- جاهز.
- يساعدك تفحص البيانات بسرعة.
- جيد أثناء التطوير.
- لا يحتاج frontend.

Flutter أو dashboard منفصل يمكن أن يستخدم API لاحقا، لكن Django Admin يظل أداة قوية للمطور.

---

## 21. لماذا كتبنا Tests؟

الاختبارات تتأكد أن أهم القواعد لا تنكسر.

اختبرنا:

- رقم الهاتف المصري.
- الاسم حروف فقط.
- قوة الباسورد.
- قبول الشروط للمريض.
- منع تكرار الإيميل.
- snapshot للأسعار.
- قبول الممرض للطلب.
- منع الممرض من قبول طلبين في نفس الوقت.
- تعليم الإشعار كمقروء.

### لماذا لم نختبر كل شيء؟

لأن المشروع v1. بدأنا بأهم business rules. لاحقا يمكن زيادة الاختبارات تدريجيا.

---

## 22. كيف تقرأ المشروع كمبتدئ؟

ابدأ بهذا الترتيب:

1. اقرأ `PROJECT_DOCUMENTATION.md`.
2. افتح `config/settings/base.py` لتفهم الإعدادات.
3. افتح `apps/accounts/models.py` لفهم المستخدمين.
4. افتح `apps/orders/models.py` لفهم الطلبات.
5. افتح `apps/orders/services.py` لفهم business logic.
6. افتح `apps/orders/views.py` لفهم endpoints.
7. افتح `tests/test_api.py` لترى أمثلة عملية.

---

## 23. كيف تضيف Feature جديدة؟

مثال: إضافة كوبون خصم.

لا تبدأ مباشرة في view. فكر بهذا الترتيب:

1. هل نحتاج Model جديد؟ مثلا `Coupon`.
2. هل نحتاج fields في Order؟ مثلا `discount_amount`.
3. هل السعر يجب أن يكون snapshot؟ غالبا نعم.
4. أين business logic؟ في service layer.
5. ما validation المطلوب؟ في serializer.
6. من له صلاحية استخدامه؟ في permissions أو view.
7. ما الاختبارات المطلوبة؟

هذه الطريقة تمنع الفوضى.

---

## 24. أخطاء شائعة يجب تجنبها

- لا تضع password في response.
- لا تجعل المريض يرى طلبات غيره.
- لا تجعل الممرض غير المعتمد يقبل طلبات.
- لا تحسب أسعار الطلب القديم من أسعار الخدمات الحالية.
- لا تكرر validation في أكثر من مكان.
- لا تضع SECRET_KEY أو database password في GitHub.
- لا تعتمد على frontend فقط في الصلاحيات. Backend يجب أن يحمي نفسه.

---

## 25. ملخص فلسفة التصميم

اخترنا بنية بسيطة لكنها قابلة للتوسع:

- Django للتنظيم والأمان.
- DRF لبناء API واضح.
- PostgreSQL للبيانات الحقيقية.
- JWT لأنه مناسب لتطبيق Flutter.
- Custom User لأن login بالإيميل والأدوار مهمة.
- Service Layer لأن business rules ليست CRUD فقط.
- Notifications منفصلة لأنها ستكبر لاحقا.
- Tests للقواعد الحساسة.
- Documentation حتى يستطيع المبتدئ فهم المشروع وليس فقط تشغيله.

الفكرة الأساسية: الكود يجب أن يكون واضحا اليوم، وقابلا للتطوير غدا.
