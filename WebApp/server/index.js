const express = require('express')
const app = express()
const cors = require('cors')
var router   =   express.Router();
const mongoose = require('mongoose')
const User = require('./models/user.model')
const CollectionStatus = require('./models/collectionstatus')
const RequestStatus = require('./models/requeststatus');
const jwt = require('jsonwebtoken')
const bcrypt = require('bcryptjs')

app.use(cors())
app.use(express.json())

mongoose.connect('mongodb://localhost:27017/ifp-petro-webapp')

app.post('/api/register', async (req,res) => {
    console.log(req.body)
    try{
        const newPassword = await bcrypt.hash(req.body.password, 10)
        await User.create({
            name: req.body.name,
            compname: req.body.compname,
            contact: req.body.contact,
            email: req.body.email,
            password: newPassword,
            address: req.body.street +", "+ req.body.city +", "+ req.body.state +", "+ req.body.zipcode +", "+req.body.country,
        })
        res.json({status: 'ok'})
    }
    catch (err){
        res.json({status: 'error', error: 'Duplicate email'})
    }
})

app.post('/api/recyclerdash', async (req,res) => {
    console.log(req.body)
    try{
        await CollectionStatus.create({
            date: req.body.date,
            customer: req.body.customer,
            customer_id: req.body.customer_id,
            volume: req.body.volume,
        })
        res.json({status: 'ok'})
    }
    catch (err){
        res.json({status: 'error', error: 'Invalid Collection Data'})
    }
})

app.get("/api/recyclerdash", (req, res) => {
    CollectionStatus.find({})
        .then((items) => res.json(items))
        .catch((err) => console.log(err.Message)); // DO NT FORGET TO CHANGE TO RequestStatus
    });

app.post('/api/login', async (req,res) => {
    
    const user = await User.findOne({
        email: req.body.email,
    })
    if(!user){
        return { status: 'error', error: 'User not found' }
    }
    const isPasswordValid = await bcrypt.compare(req.body.password, user.password)
    if(isPasswordValid) {
        const token = jwt.sign({
            name: user.name,
            email: user.email,
        }, 'secret123') // this secret123 should be something very secure
        return res.json({status: 'ok', user: token})
    }
    else{
        return res.json({status: 'error', user: false})
    }
})

app.get('/api/userdashboard', async (req, res) => {
	const token = req.headers['x-access-token']

	try {
		const decoded = jwt.verify(token, 'secret123')
		const email = decoded.email
		const user = await User.findOne({ email: email })

		return res.json({ status: 'ok', quote: user.quote })
	} catch (error) {
		console.log(error)
		res.json({ status: 'error', error: 'invalid token' })
	}
})

app.post('/api/userdashboard', async (req,res) => {
    
    const token = req.headers['x-access-token']

    try{
        const decoded = jwt.verify(token, 'secret123')
        const email = decoded.email
        await User.updateOne(
            { email: email }, 
            { $set: { quote: req.body.quote}}
        )

        return res.json({status: 'ok'})
    }
    catch(error){
        console.log(error)
        res.json({status: 'error', error: 'invalid token'})
    }
})

app.listen(1337, () => {
    console.log('server started on port 1337')
})